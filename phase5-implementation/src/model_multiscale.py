"""
Multi-Scale Feature Extractor for Large Maps

Processes three observation scales:
- Global map (128×128): Strategic overview
- Local map (128×128): Tactical awareness
- Tactical map (64×64): Precise control

Uses attention to fuse multi-scale features.
"""

import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from gymnasium import spaces
import numpy as np


class MultiScaleExtractor(BaseFeaturesExtractor):
    """
    Multi-scale feature extractor for large map observations.

    Architecture:
    1. Global CNN: Process 128×128 global map
    2. Local CNN: Process 128×128 local map
    3. Tactical CNN: Process 64×64 tactical map
    4. Global features MLP: Process scalar features
    5. Cross-attention fusion: Combine all scales
    6. Output: Unified feature vector
    """

    def __init__(
        self,
        observation_space: spaces.Dict,
        features_dim: int = 512
    ):
        # Calculate total features before fusion
        # Each CNN produces 256 features, global MLP produces 128
        # Total before fusion: 256*3 + 128 = 896
        super().__init__(observation_space, features_dim)

        # Get input dimensions
        global_map_shape = observation_space['global_map'].shape  # (128, 128, 5*frame_stack)
        local_map_shape = observation_space['local_map'].shape    # (128, 128, 5*frame_stack)
        tactical_map_shape = observation_space['tactical_map'].shape  # (64, 64, 5*frame_stack)
        global_features_shape = observation_space['global'].shape  # (16*frame_stack,)

        n_input_channels_global = global_map_shape[2]
        n_input_channels_local = local_map_shape[2]
        n_input_channels_tactical = tactical_map_shape[2]
        n_global_features = global_features_shape[0]

        # Global map CNN (strategic overview)
        self.global_cnn = nn.Sequential(
            # 128×128×C → 64×64×32
            nn.Conv2d(n_input_channels_global, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(32),

            # 64×64×32 → 32×32×64
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(64),

            # 32×32×64 → 16×16×128
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(128),

            # 16×16×128 → 8×8×128
            nn.Conv2d(128, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(128),

            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU()
        )

        # Local map CNN (tactical awareness)
        self.local_cnn = nn.Sequential(
            # 128×128×C → 64×64×32
            nn.Conv2d(n_input_channels_local, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(32),

            # 64×64×32 → 32×32×64
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(64),

            # 32×32×64 → 16×16×128
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(128),

            # 16×16×128 → 8×8×128
            nn.Conv2d(128, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(128),

            nn.Flatten(),
            nn.Linear(128 * 8 * 8, 256),
            nn.ReLU()
        )

        # Tactical map CNN (precise control) - smaller input
        self.tactical_cnn = nn.Sequential(
            # 64×64×C → 32×32×32
            nn.Conv2d(n_input_channels_tactical, 32, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(32),

            # 32×32×32 → 16×16×64
            nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(64),

            # 16×16×64 → 8×8×128
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(128),

            # 8×8×128 → 4×4×128
            nn.Conv2d(128, 128, kernel_size=3, stride=2, padding=1),
            nn.ReLU(),
            nn.BatchNorm2d(128),

            nn.Flatten(),
            nn.Linear(128 * 4 * 4, 256),
            nn.ReLU()
        )

        # Global features MLP
        self.global_mlp = nn.Sequential(
            nn.Linear(n_global_features, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        # Cross-attention for fusing multi-scale features
        # Query: global features, Key/Value: spatial features
        self.attention = nn.MultiheadAttention(
            embed_dim=256,
            num_heads=4,
            batch_first=True
        )

        # Projection layers for attention
        self.global_proj = nn.Linear(256, 256)
        self.local_proj = nn.Linear(256, 256)
        self.tactical_proj = nn.Linear(256, 256)
        self.feature_proj = nn.Linear(128, 256)

        # Final fusion layer
        # Input: 256 (global) + 256 (local) + 256 (tactical) + 128 (features) = 896
        # But after attention: 256 (fused spatial) + 128 (features) = 384
        self.fusion = nn.Sequential(
            nn.Linear(256 + 128, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, features_dim),
            nn.ReLU()
        )

    def forward(self, observations: dict) -> torch.Tensor:
        """
        Process multi-scale observations.

        Args:
            observations: Dict with keys:
                - 'global_map': (B, H, W, C) -> needs transpose to (B, C, H, W)
                - 'local_map': (B, H, W, C)
                - 'tactical_map': (B, H, W, C)
                - 'global': (B, F)

        Returns:
            features: (B, features_dim)
        """
        # Extract and transpose spatial inputs (B, H, W, C) -> (B, C, H, W)
        global_map = observations['global_map'].permute(0, 3, 1, 2)
        local_map = observations['local_map'].permute(0, 3, 1, 2)
        tactical_map = observations['tactical_map'].permute(0, 3, 1, 2)
        global_features = observations['global']

        # Process each scale
        global_spatial = self.global_cnn(global_map)      # (B, 256)
        local_spatial = self.local_cnn(local_map)          # (B, 256)
        tactical_spatial = self.tactical_cnn(tactical_map) # (B, 256)
        global_vec = self.global_mlp(global_features)     # (B, 128)

        # Project to attention space
        global_proj = self.global_proj(global_spatial)     # (B, 256)
        local_proj = self.local_proj(local_spatial)        # (B, 256)
        tactical_proj = self.tactical_proj(tactical_spatial) # (B, 256)
        feature_proj = self.feature_proj(global_vec)       # (B, 256)

        # Stack spatial features as key/value: (B, 3, 256)
        spatial_kv = torch.stack([global_proj, local_proj, tactical_proj], dim=1)

        # Use global features as query: (B, 1, 256)
        query = feature_proj.unsqueeze(1)

        # Cross-attention: which spatial scale to focus on?
        attended, attention_weights = self.attention(
            query, spatial_kv, spatial_kv
        )  # (B, 1, 256)

        # Squeeze attention output
        attended = attended.squeeze(1)  # (B, 256)

        # Concatenate attended spatial features with global features
        fused = torch.cat([attended, global_vec], dim=1)  # (B, 256+128=384)

        # Final fusion
        output = self.fusion(fused)  # (B, features_dim)

        return output
