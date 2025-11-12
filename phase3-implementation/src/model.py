"""
Neural Network Architecture for Phase 3 - Battle Royale

CNN + MLP architecture (~500K parameters):
- CNN branch: Process 128×128×5 map features
- MLP branch: Process 16 global features
- Fusion layer: Combine both branches
- Actor-Critic heads: Policy and value function
"""

import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from gymnasium import spaces
from typing import Dict


class BattleRoyaleExtractor(BaseFeaturesExtractor):
    """
    Feature extractor combining CNN (map) and MLP (global features).

    Architecture:
    - CNN: 128×128×5 → 512 features
    - MLP: 16 → 128 features
    - Fusion: 640 → 256 features
    """

    def __init__(self, observation_space: spaces.Dict, features_dim: int = 256):
        super().__init__(observation_space, features_dim)

        # Extract input shapes
        map_shape = observation_space['map'].shape  # (128, 128, 5)
        global_shape = observation_space['global'].shape  # (16,)

        # CNN for map processing
        # Input: 128×128×5
        # Conv1: 128×128×5 → 32×32×32
        # Conv2: 32×32×32 → 16×16×64
        # Conv3: 16×16×64 → 14×14×64
        # Flatten: 14×14×64 = 12,544
        # FC: 12,544 → 512
        self.cnn = nn.Sequential(
            nn.Conv2d(map_shape[2], 32, kernel_size=8, stride=4, padding=2),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=0),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(12544, 512),
            nn.ReLU()
        )

        # MLP for global features
        # Input: 16
        # FC1: 16 → 128
        # FC2: 128 → 128
        self.mlp = nn.Sequential(
            nn.Linear(global_shape[0], 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        # Fusion layer
        # Input: 512 + 128 = 640
        # Output: features_dim (default 256)
        self.fusion = nn.Sequential(
            nn.Linear(640, features_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

    def forward(self, observations: Dict[str, torch.Tensor]) -> torch.Tensor:
        """
        Forward pass through feature extractor.

        Args:
            observations: Dict with 'map' and 'global' tensors

        Returns:
            Combined features tensor [batch_size, features_dim]
        """
        # Process map through CNN
        # Input shape: [batch, height, width, channels]
        # Need to permute to: [batch, channels, height, width]
        map_input = observations['map'].permute(0, 3, 1, 2)
        map_features = self.cnn(map_input)

        # Process global features through MLP
        global_features = self.mlp(observations['global'])

        # Concatenate and fuse
        combined = torch.cat([map_features, global_features], dim=1)
        output = self.fusion(combined)

        return output


class BattleRoyalePolicy(nn.Module):
    """
    Complete policy network with actor-critic architecture.

    This is a standalone implementation for reference.
    In practice, we use SB3's PPO with BattleRoyaleExtractor.
    """

    def __init__(self):
        super().__init__()

        # CNN for map
        self.cnn = nn.Sequential(
            nn.Conv2d(5, 32, 8, 4, 2),
            nn.ReLU(),
            nn.Conv2d(32, 64, 4, 2, 1),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, 1, 0),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(12544, 512),
            nn.ReLU()
        )

        # MLP for global
        self.mlp = nn.Sequential(
            nn.Linear(16, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        # Fusion
        self.fusion = nn.Sequential(
            nn.Linear(640, 256),
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
        Forward pass through complete policy.

        Args:
            obs: Dict with 'map' [B, 128, 128, 5] and 'global' [B, 16]

        Returns:
            action_logits: [B, 45]
            value: [B, 1]
        """
        # Process map
        map_input = obs['map'].permute(0, 3, 1, 2)
        map_feat = self.cnn(map_input)

        # Process global
        global_feat = self.mlp(obs['global'])

        # Combine
        combined = torch.cat([map_feat, global_feat], dim=1)
        shared = self.fusion(combined)

        # Get outputs
        action_logits = self.actor(shared)
        value = self.critic(shared)

        return action_logits, value


def count_parameters(model: nn.Module) -> int:
    """
    Count trainable parameters in model.

    Args:
        model: PyTorch model

    Returns:
        Number of trainable parameters
    """
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Test the architecture
    print("Testing BattleRoyale Policy Architecture")
    print("=" * 50)

    # Create model
    model = BattleRoyalePolicy()

    # Count parameters
    total_params = count_parameters(model)
    print(f"\nTotal parameters: {total_params:,}")

    # Component-wise parameter count
    cnn_params = count_parameters(model.cnn)
    mlp_params = count_parameters(model.mlp)
    fusion_params = count_parameters(model.fusion)
    actor_params = count_parameters(model.actor)
    critic_params = count_parameters(model.critic)

    print(f"\nComponent breakdown:")
    print(f"  CNN branch:    {cnn_params:,}")
    print(f"  MLP branch:    {mlp_params:,}")
    print(f"  Fusion layer:  {fusion_params:,}")
    print(f"  Actor head:    {actor_params:,}")
    print(f"  Critic head:   {critic_params:,}")

    # Test forward pass
    print(f"\nTesting forward pass...")
    batch_size = 4

    test_obs = {
        'map': torch.randn(batch_size, 128, 128, 5),
        'global': torch.randn(batch_size, 16)
    }

    with torch.no_grad():
        action_logits, value = model(test_obs)

    print(f"  Input map shape:    {test_obs['map'].shape}")
    print(f"  Input global shape: {test_obs['global'].shape}")
    print(f"  Output action logits: {action_logits.shape}")
    print(f"  Output value:       {value.shape}")

    print(f"\nArchitecture test passed!")
