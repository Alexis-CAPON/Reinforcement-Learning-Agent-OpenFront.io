"""
Multi-Scale Feature Extractor with Spatial Attention

Enhanced version with attention mechanisms inspired by AlphaStar.
Each spatial scale has attention layers to focus on important regions.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from gymnasium import spaces
import numpy as np


class SpatialAttention(nn.Module):
    """
    Spatial attention module.

    Learns to generate attention weights over spatial dimensions,
    allowing the network to focus on important regions (borders, threats, etc.)
    """

    def __init__(self, in_channels: int):
        super().__init__()

        # Generate attention map
        self.attention_conv = nn.Sequential(
            nn.Conv2d(in_channels, in_channels // 4, kernel_size=1),
            nn.ReLU(),
            nn.Conv2d(in_channels // 4, 1, kernel_size=1),
        )

    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) feature maps

        Returns:
            attended: (B, C, H, W) attention-weighted features
            attention_weights: (B, 1, H, W) attention map (for visualization)
        """
        B, C, H, W = x.shape

        # Generate attention weights
        attention = self.attention_conv(x)  # (B, 1, H, W)

        # Spatial softmax (across H×W dimensions)
        attention = attention.view(B, 1, -1)  # (B, 1, H*W)
        attention = F.softmax(attention, dim=2)  # Normalize across spatial dims
        attention = attention.view(B, 1, H, W)  # (B, 1, H, W)

        # Apply attention
        attended = x * attention  # Broadcast: (B, C, H, W) * (B, 1, H, W)

        return attended, attention


class ChannelAttention(nn.Module):
    """
    Channel attention module.

    Learns which feature channels are most important
    (e.g., focus on "enemy territory" channel vs "neutral" channel).
    """

    def __init__(self, in_channels: int, reduction: int = 8):
        super().__init__()

        # Global average pooling to get channel importance
        self.avg_pool = nn.AdaptiveAvgPool2d(1)

        # FC layers to generate channel weights
        self.fc = nn.Sequential(
            nn.Linear(in_channels, in_channels // reduction, bias=False),
            nn.ReLU(),
            nn.Linear(in_channels // reduction, in_channels, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) feature maps

        Returns:
            attended: (B, C, H, W) channel-weighted features
            channel_weights: (B, C) channel attention weights
        """
        B, C, _, _ = x.shape

        # Global pooling: (B, C, H, W) -> (B, C, 1, 1)
        pooled = self.avg_pool(x)
        pooled = pooled.view(B, C)  # (B, C)

        # Generate channel weights
        channel_weights = self.fc(pooled)  # (B, C)

        # Apply channel attention
        channel_weights = channel_weights.view(B, C, 1, 1)  # (B, C, 1, 1)
        attended = x * channel_weights  # Broadcast

        return attended, channel_weights.squeeze()


class AttentionCNNBranch(nn.Module):
    """
    CNN branch with both spatial and channel attention.

    Used for each scale (global, local, tactical).
    """

    def __init__(
        self,
        in_channels: int,
        input_size: int,  # 128 or 64
        output_features: int = 256
    ):
        super().__init__()

        self.input_size = input_size

        # Layer 1: input_size -> input_size/2
        self.conv1 = nn.Conv2d(in_channels, 32, kernel_size=3, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.spatial_attn1 = SpatialAttention(32)

        # Layer 2: input_size/2 -> input_size/4
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.channel_attn2 = ChannelAttention(64)

        # Layer 3: input_size/4 -> input_size/8
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.spatial_attn3 = SpatialAttention(128)

        # Layer 4: input_size/8 -> input_size/16
        self.conv4 = nn.Conv2d(128, 128, kernel_size=3, stride=2, padding=1)
        self.bn4 = nn.BatchNorm2d(128)
        self.channel_attn4 = ChannelAttention(128)

        # Calculate final spatial size
        final_size = input_size // 16

        # Flatten and project
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128 * final_size * final_size, output_features),
            nn.ReLU()
        )

    def forward(self, x):
        """
        Args:
            x: (B, C, H, W) input

        Returns:
            features: (B, output_features) extracted features
        """
        # Layer 1 with spatial attention
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x, _ = self.spatial_attn1(x)  # Focus on important spatial regions

        # Layer 2 with channel attention
        x = self.conv2(x)
        x = self.bn2(x)
        x = F.relu(x)
        x, _ = self.channel_attn2(x)  # Focus on important channels

        # Layer 3 with spatial attention
        x = self.conv3(x)
        x = self.bn3(x)
        x = F.relu(x)
        x, _ = self.spatial_attn3(x)  # Focus on important regions again

        # Layer 4 with channel attention
        x = self.conv4(x)
        x = self.bn4(x)
        x = F.relu(x)
        x, _ = self.channel_attn4(x)  # Final channel attention

        # Flatten and project
        features = self.fc(x)

        return features


class MultiScaleExtractorWithAttention(BaseFeaturesExtractor):
    """
    Multi-scale feature extractor with spatial and channel attention.

    Architecture inspired by AlphaStar:
    - Global CNN: Strategic overview with attention
    - Local CNN: Tactical awareness with attention
    - Tactical CNN: Precise control with attention
    - Cross-attention fusion: Combine scales intelligently
    """

    def __init__(
        self,
        observation_space: spaces.Dict,
        features_dim: int = 512
    ):
        super().__init__(observation_space, features_dim)

        # Get input dimensions
        global_map_shape = observation_space['global_map'].shape
        local_map_shape = observation_space['local_map'].shape
        tactical_map_shape = observation_space['tactical_map'].shape
        global_features_shape = observation_space['global'].shape

        n_input_channels_global = global_map_shape[2]
        n_input_channels_local = local_map_shape[2]
        n_input_channels_tactical = tactical_map_shape[2]
        n_global_features = global_features_shape[0]

        # Attention-based CNN branches for each scale
        self.global_cnn = AttentionCNNBranch(
            in_channels=n_input_channels_global,
            input_size=128,
            output_features=256
        )

        self.local_cnn = AttentionCNNBranch(
            in_channels=n_input_channels_local,
            input_size=128,
            output_features=256
        )

        self.tactical_cnn = AttentionCNNBranch(
            in_channels=n_input_channels_tactical,
            input_size=64,
            output_features=256
        )

        # Global features MLP
        self.global_mlp = nn.Sequential(
            nn.Linear(n_global_features, 128),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(128, 128),
            nn.ReLU()
        )

        # Cross-attention for fusing multi-scale features
        # Query: global features, Key/Value: spatial features
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=256,
            num_heads=8,  # More heads for better attention
            dropout=0.1,
            batch_first=True
        )

        # Projection layers for attention
        self.global_proj = nn.Linear(256, 256)
        self.local_proj = nn.Linear(256, 256)
        self.tactical_proj = nn.Linear(256, 256)
        self.feature_proj = nn.Linear(128, 256)

        # Scale importance weights (learnable)
        self.scale_weights = nn.Parameter(torch.ones(3) / 3)  # Initialize uniformly

        # Final fusion MLP
        # Input: 256 (attended spatial) + 128 (global features) = 384
        self.fusion = nn.Sequential(
            nn.Linear(384, 512),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(512, features_dim),
            nn.ReLU()
        )

        # Layer normalization for stability
        self.layer_norm = nn.LayerNorm(features_dim)

    def forward(self, observations: dict) -> torch.Tensor:
        """
        Process multi-scale observations with attention.

        Args:
            observations: Dict with keys:
                - 'global_map': (B, H, W, C)
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

        # Process each scale through attention-based CNNs
        global_spatial = self.global_cnn(global_map)      # (B, 256)
        local_spatial = self.local_cnn(local_map)          # (B, 256)
        tactical_spatial = self.tactical_cnn(tactical_map) # (B, 256)
        global_vec = self.global_mlp(global_features)     # (B, 128)

        # Project to attention space
        global_proj = self.global_proj(global_spatial)     # (B, 256)
        local_proj = self.local_proj(local_spatial)        # (B, 256)
        tactical_proj = self.tactical_proj(tactical_spatial) # (B, 256)
        feature_proj = self.feature_proj(global_vec)       # (B, 256)

        # Apply learnable scale importance weights
        # (Allows model to learn which scales are most important)
        scale_weights = F.softmax(self.scale_weights, dim=0)
        global_proj = global_proj * scale_weights[0]
        local_proj = local_proj * scale_weights[1]
        tactical_proj = tactical_proj * scale_weights[2]

        # Stack spatial features as key/value: (B, 3, 256)
        spatial_kv = torch.stack([global_proj, local_proj, tactical_proj], dim=1)

        # Use global features as query: (B, 1, 256)
        query = feature_proj.unsqueeze(1)

        # Cross-attention: which spatial scale is most relevant?
        attended, attention_weights = self.cross_attention(
            query, spatial_kv, spatial_kv
        )  # attended: (B, 1, 256), weights: (B, 1, 3)

        # Squeeze attention output
        attended = attended.squeeze(1)  # (B, 256)

        # Concatenate attended spatial features with global features
        fused = torch.cat([attended, global_vec], dim=1)  # (B, 384)

        # Final fusion
        output = self.fusion(fused)  # (B, features_dim)

        # Layer normalization for training stability
        output = self.layer_norm(output)

        return output
