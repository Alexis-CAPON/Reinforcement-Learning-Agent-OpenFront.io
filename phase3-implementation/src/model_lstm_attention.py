"""
LSTM + Attention Architecture for Phase 3 - Battle Royale

Key improvements over frame stacking:
- LSTM provides long-term temporal memory (100+ steps)
- Attention mechanisms focus on strategic map regions
- Can learn temporal patterns: "expanding too fast → consolidate"

Architecture:
- CNN (128×128×5) → 256 features (spatial attention)
- MLP (16 global) → 128 features
- Cross-Attention Fusion → 128 features
- Combined → 256 features
- LSTM (256 → 256) ← MEMORY LAYER
- Actor (256 → 45 actions)
- Critic (256 → 1 value)

Total: ~800K parameters
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

    Highlights:
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
        attention = torch.sigmoid(self.conv(x))  # [B, 1, H, W]
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
        Q = self.map_to_q(map_feat)
        K = self.global_to_k(global_feat)
        V = self.global_to_v(global_feat)

        # Attention
        attn_scores = torch.sum(Q * K, dim=-1, keepdim=True) * self.scale
        attn_weights = torch.softmax(attn_scores, dim=-1)
        attended = attn_weights * V

        return self.out(attended)


class EfficientCNN(nn.Module):
    """
    Efficient CNN with Global Average Pooling and spatial attention.

    Architecture:
    - 3 conv blocks with spatial attention
    - Global Average Pooling (reduces params by 13x)
    - Output projection
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

        # Global Average Pooling + projection
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(128, out_features)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through efficient CNN."""
        x = F.relu(self.bn1(self.conv1(x)))
        x = self.attn1(x)

        x = F.relu(self.bn2(self.conv2(x)))
        x = self.attn2(x)

        x = F.relu(self.bn3(self.conv3(x)))
        x = self.attn3(x)

        x = self.gap(x)
        x = torch.flatten(x, 1)
        x = F.relu(self.fc(x))

        return x


class BattleRoyaleExtractorLSTM(BaseFeaturesExtractor):
    """
    Feature extractor for RecurrentPPO with LSTM support.

    NO frame stacking - LSTM provides temporal memory!

    Architecture:
    - CNN: 128×128×5 → 256 features
    - MLP: 16 global → 128 features
    - Cross-Attention Fusion → 128 features
    - Combined → 256 features (fed to LSTM in RecurrentPPO)

    RecurrentPPO will add:
    - LSTM: 256 → 256 (built into policy)
    - Actor/Critic heads
    """

    def __init__(self, observation_space: spaces.Dict, features_dim: int = 256):
        super().__init__(observation_space, features_dim)

        # Get shapes (should be single-frame, no stacking!)
        map_shape = observation_space['map'].shape  # (128, 128, 5)
        global_shape = observation_space['global'].shape  # (16,)

        # Efficient CNN with spatial attention
        self.cnn = EfficientCNN(in_channels=map_shape[2], out_features=256)

        # MLP for global features
        self.mlp = nn.Sequential(
            nn.Linear(global_shape[0], 128),
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
            nn.Linear(256 + 128 + 128, features_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

    def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Forward pass.

        Args:
            observations: Dict with 'map' and 'global' tensors

        Returns:
            Combined features [batch_size, features_dim] → Fed to LSTM
        """
        # Process map
        map_input = observations['map'].permute(0, 3, 1, 2).contiguous()
        map_features = self.cnn(map_input)

        # Process global
        global_features = self.mlp(observations['global'])

        # Cross-attention
        cross_attn_features = self.cross_attn(map_features, global_features)

        # Combine
        combined = torch.cat([map_features, global_features, cross_attn_features], dim=1)
        output = self.fusion(combined)

        return output


def count_parameters(model: nn.Module) -> int:
    """Count trainable parameters in model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    print("Testing LSTM Feature Extractor")
    print("=" * 70)

    # Create dummy observation space (NO frame stacking)
    obs_space = spaces.Dict({
        'map': spaces.Box(0, 1, (128, 128, 5), dtype='float32'),
        'global': spaces.Box(-1, 1, (16,), dtype='float32')
    })

    # Create feature extractor
    extractor = BattleRoyaleExtractorLSTM(obs_space, features_dim=256)

    # Count parameters
    total_params = count_parameters(extractor)
    print(f"\n✅ Feature extractor parameters: {total_params:,}")

    # Test forward pass
    print(f"\n🧪 Testing forward pass...")
    batch_size = 4
    test_obs = {
        'map': torch.randn(batch_size, 128, 128, 5),
        'global': torch.randn(batch_size, 16)
    }

    with torch.no_grad():
        features = extractor(test_obs)

    print(f"  Input map shape:    {test_obs['map'].shape}")
    print(f"  Input global shape: {test_obs['global'].shape}")
    print(f"  Output features:    {features.shape}")

    print(f"\n💡 These features will be fed to LSTM in RecurrentPPO")
    print(f"   LSTM will add ~200K parameters (256×256 hidden state)")
    print(f"   Total model: ~{total_params + 200_000:,} parameters")

    print(f"\n✅ LSTM feature extractor ready!")
