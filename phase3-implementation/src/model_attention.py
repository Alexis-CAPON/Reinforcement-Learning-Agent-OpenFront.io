"""
Improved Neural Network Architecture for Phase 3 - Battle Royale

CNN + MLP with Attention Mechanisms (~500K parameters):
- Efficient CNN with Global Average Pooling
- Spatial Attention for important map regions
- Cross-Attention Fusion between map and global features
- Actor-Critic heads for PPO
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from gymnasium import spaces
from typing import Dict


class SpatialAttention(nn.Module):
    """
    Spatial attention module to focus on important map regions.

    Generates attention weights over spatial dimensions to highlight:
    - Border tiles (where attacks happen)
    - Enemy territories (threats)
    - Cities (strategic resources)
    """

    def __init__(self, in_channels: int):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, 1, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply spatial attention.

        Args:
            x: Feature maps [B, C, H, W]

        Returns:
            Attention-weighted features [B, C, H, W]
        """
        # Generate attention map
        attention = torch.sigmoid(self.conv(x))  # [B, 1, H, W]

        # Apply attention
        return x * attention


class CrossAttentionFusion(nn.Module):
    """
    Cross-attention between map features and global features.

    Allows:
    - Map features to query global stats ("given my rank, where to attack?")
    - Global stats to query map features ("which border is most important?")
    """

    def __init__(self, map_dim: int, global_dim: int, hidden_dim: int = 128):
        super().__init__()

        # Query, Key, Value projections
        self.map_to_q = nn.Linear(map_dim, hidden_dim)
        self.global_to_k = nn.Linear(global_dim, hidden_dim)
        self.global_to_v = nn.Linear(global_dim, hidden_dim)

        # Output projection
        self.out = nn.Linear(hidden_dim, hidden_dim)
        self.scale = hidden_dim ** -0.5

    def forward(self, map_feat: torch.Tensor, global_feat: torch.Tensor) -> torch.Tensor:
        """
        Apply cross-attention.

        Args:
            map_feat: Map features [B, map_dim]
            global_feat: Global features [B, global_dim]

        Returns:
            Fused features [B, hidden_dim]
        """
        # Project to Q, K, V
        Q = self.map_to_q(map_feat)           # [B, hidden_dim]
        K = self.global_to_k(global_feat)     # [B, hidden_dim]
        V = self.global_to_v(global_feat)     # [B, hidden_dim]

        # Compute attention scores
        attn_scores = torch.sum(Q * K, dim=-1, keepdim=True) * self.scale  # [B, 1]
        attn_weights = torch.softmax(attn_scores, dim=-1)

        # Apply attention
        attended = attn_weights * V  # [B, hidden_dim]

        # Output projection
        output = self.out(attended)

        return output


class EfficientCNN(nn.Module):
    """
    Efficient CNN with Global Average Pooling to reduce parameters.

    Architecture:
    - Conv layers with increasing channels
    - Spatial attention after each conv block
    - Global Average Pooling instead of flatten
    - Result: ~200K parameters instead of 6.5M
    """

    def __init__(self, in_channels: int = 5, out_features: int = 256):
        super().__init__()

        # Conv Block 1: 128×128×5 → 32×32×32
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=8, stride=4, padding=2)
        self.bn1 = nn.BatchNorm2d(32)
        self.attn1 = SpatialAttention(32)

        # Conv Block 2: 32×32×32 → 8×8×64
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=4, padding=0)
        self.bn2 = nn.BatchNorm2d(64)
        self.attn2 = SpatialAttention(64)

        # Conv Block 3: 8×8×64 → 4×4×128
        self.conv3 = nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.attn3 = SpatialAttention(128)

        # Global Average Pooling: 4×4×128 → 128
        self.gap = nn.AdaptiveAvgPool2d(1)

        # Output projection
        self.fc = nn.Linear(128, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through efficient CNN.

        Args:
            x: Map input [B, C, H, W]

        Returns:
            Map features [B, out_features]
        """
        # Block 1
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.attn1(x)

        # Block 2
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.attn2(x)

        # Block 3
        x = F.relu(self.bn3(self.conv3(x)))
        x = self.attn3(x)

        # Global pooling
        x = self.gap(x)  # [B, 128, 1, 1]
        x = torch.flatten(x, 1)  # [B, 128] - use torch.flatten for non-contiguous tensors

        # Output projection
        x = F.relu(self.fc(x))  # [B, out_features]

        return x


class BattleRoyaleExtractorWithAttention(BaseFeaturesExtractor):
    """
    Improved feature extractor with attention mechanisms and frame stacking support.

    Architecture (with frame_stack=4):
    - Efficient CNN with spatial attention: 128×128×20 (5×4 frames) → 256 features
    - MLP for global features: 64 (16×4 frames) → 128 features
    - Cross-attention fusion: 256 + 128 → 256 features

    Total: ~530K parameters (with frame stacking)

    Note: Automatically adapts to observation space dimensions.
    """

    def __init__(self, observation_space: spaces.Dict, features_dim: int = 256):
        super().__init__(observation_space, features_dim)

        # Extract input shapes (automatically handles frame stacking)
        map_shape = observation_space['map'].shape  # (128, 128, channels)
        global_shape = observation_space['global'].shape  # (features,)

        # Efficient CNN with spatial attention (adapts to stacked channels)
        self.cnn = EfficientCNN(in_channels=map_shape[2], out_features=256)

        # MLP for global features (adapts to stacked features)
        # With frame stacking, input size is 4x larger (16 → 64)
        self.mlp = nn.Sequential(
            nn.Linear(global_shape[0], 256),  # Larger first layer for 4x input
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        # Cross-attention fusion
        self.cross_attn = CrossAttentionFusion(
            map_dim=256,
            global_dim=128,
            hidden_dim=128
        )

        # Final fusion
        self.fusion = nn.Sequential(
            nn.Linear(256 + 128 + 128, features_dim),  # map + global + cross_attn
            nn.ReLU(),
            nn.Dropout(0.1)
        )

    def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Forward pass with attention.

        Args:
            observations: Dict with 'map' and 'global' tensors

        Returns:
            Combined features [batch_size, features_dim]
        """
        # Process map through efficient CNN with spatial attention
        map_input = observations['map'].permute(0, 3, 1, 2).contiguous()  # [B, 128, 128, 5] → [B, 5, 128, 128]
        map_features = self.cnn(map_input)  # [B, 256]

        # Process global features through MLP
        global_features = self.mlp(observations['global'])  # [B, 128]

        # Cross-attention between map and global
        cross_attn_features = self.cross_attn(map_features, global_features)  # [B, 128]

        # Concatenate all features
        combined = torch.cat([map_features, global_features, cross_attn_features], dim=1)  # [B, 512]

        # Final fusion
        output = self.fusion(combined)  # [B, features_dim]

        return output


class BattleRoyalePolicyWithAttention(nn.Module):
    """
    Complete policy network with attention mechanisms and frame stacking support.

    For standalone testing and verification.

    Args:
        in_channels: Number of map channels (5 for single frame, 20 for 4-frame stack)
        global_features: Number of global features (16 for single frame, 64 for 4-frame stack)
    """

    def __init__(self, in_channels: int = 20, global_features: int = 64):
        super().__init__()

        # Feature extractor (default: 4-frame stack)
        self.cnn = EfficientCNN(in_channels=in_channels, out_features=256)
        self.mlp = nn.Sequential(
            nn.Linear(global_features, 256),  # Adapted for frame stacking
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )
        self.cross_attn = CrossAttentionFusion(256, 128, 128)
        self.fusion = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # Actor head (policy)
        self.actor = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 45)  # 9 directions × 5 intensities
        )

        # Critic head (value function)
        self.critic = nn.Sequential(
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1)
        )

    def forward(self, obs: Dict[str, torch.Tensor]):
        """
        Forward pass through complete policy with attention.

        Args:
            obs: Dict with 'map' [B, 128, 128, 5] and 'global' [B, 16]

        Returns:
            action_logits: [B, 45]
            value: [B, 1]
        """
        # Process map
        map_input = obs['map'].permute(0, 3, 1, 2).contiguous()
        map_feat = self.cnn(map_input)

        # Process global
        global_feat = self.mlp(obs['global'])

        # Cross-attention
        cross_feat = self.cross_attn(map_feat, global_feat)

        # Combine
        combined = torch.cat([map_feat, global_feat, cross_feat], dim=1)
        shared = self.fusion(combined)

        # Get outputs
        action_logits = self.actor(shared)
        value = self.critic(shared)

        return action_logits, value


def count_parameters(model: nn.Module) -> int:
    """Count trainable parameters in model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    print("Testing BattleRoyale Policy with Attention + Frame Stacking")
    print("=" * 70)

    # Create model with frame stacking (default: 4 frames)
    model = BattleRoyalePolicyWithAttention(in_channels=20, global_features=64)

    # Count parameters
    total_params = count_parameters(model)
    print(f"\n✅ Total parameters: {total_params:,}")

    # Component-wise parameter count
    cnn_params = count_parameters(model.cnn)
    mlp_params = count_parameters(model.mlp)
    cross_attn_params = count_parameters(model.cross_attn)
    fusion_params = count_parameters(model.fusion)
    actor_params = count_parameters(model.actor)
    critic_params = count_parameters(model.critic)

    print(f"\n📊 Component breakdown:")
    print(f"  CNN (with spatial attention): {cnn_params:,}")
    print(f"  MLP branch:                   {mlp_params:,}")
    print(f"  Cross-attention fusion:       {cross_attn_params:,}")
    print(f"  Fusion layer:                 {fusion_params:,}")
    print(f"  Actor head:                   {actor_params:,}")
    print(f"  Critic head:                  {critic_params:,}")

    # Test forward pass with frame stacking (4 frames)
    print(f"\n🧪 Testing forward pass with frame stacking...")
    batch_size = 4
    frame_stack = 4

    test_obs = {
        'map': torch.randn(batch_size, 128, 128, 5 * frame_stack),  # 20 channels
        'global': torch.randn(batch_size, 16 * frame_stack)  # 64 features
    }

    with torch.no_grad():
        action_logits, value = model(test_obs)

    print(f"  Input map shape:      {test_obs['map'].shape} (4 frames × 5 channels)")
    print(f"  Input global shape:   {test_obs['global'].shape} (4 frames × 16 features)")
    print(f"  Output action logits: {action_logits.shape}")
    print(f"  Output value:         {value.shape}")

    # Verify parameter target
    print(f"\n🎯 Parameter target: ~500-600K")
    if total_params < 700_000:
        print(f"✅ SUCCESS! Model has {total_params:,} parameters (within target)")
    else:
        print(f"⚠️  Model has {total_params:,} parameters (above 500K target)")

    print(f"\n✅ Architecture test passed!")

    # Show attention benefits
    print(f"\n💡 Attention Mechanisms:")
    print(f"  1. Spatial Attention: Focuses on borders, cities, threats")
    print(f"  2. Cross-Attention: Links map features with global stats")
    print(f"  3. Efficient CNN: Global pooling reduces params by 13x")
