"""
Extract model internal state for visualization
Works with Stable-Baselines3 PPO models
"""

import numpy as np
import torch
from typing import Dict, Any, Optional, Tuple
from stable_baselines3 import PPO


class ModelStateExtractor:
    """Extract internal states from PPO model for visualization"""

    def __init__(self, model: PPO):
        self.model = model
        self.policy = model.policy

        # Action space info (Phase 3: 9 directions × 5 intensities = 45 actions)
        self.n_directions = 9  # N, NE, E, SE, S, SW, W, NW, WAIT
        self.n_intensities = 5  # 15%, 30%, 45%, 60%, 75%
        self.n_actions = 45  # Total actions

        self.direction_names = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'WAIT']
        self.intensity_values = [0.15, 0.30, 0.45, 0.60, 0.75]

    def predict_with_details(
        self,
        observation,
        deterministic: bool = True
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Predict action and extract detailed information about the prediction

        Returns:
            action: The selected action index
            details: Dictionary with:
                - direction_probs: Probability for each direction
                - intensity_probs: Probability for each intensity
                - value_estimate: Value function estimate
                - attention_weights: Attention weights (if model uses attention)
        """
        # Handle dict observation space
        if isinstance(observation, dict):
            # Convert dict observation to tensors
            obs_tensor = {
                key: torch.as_tensor(val, device=self.model.device).float().unsqueeze(0)
                for key, val in observation.items()
            }
        else:
            # Handle array observation
            obs_tensor = torch.as_tensor(observation, device=self.model.device).float()
            if obs_tensor.ndim == 1:
                obs_tensor = obs_tensor.unsqueeze(0)

        # Get action probabilities from policy
        with torch.no_grad():
            # For MultiInputActorCriticPolicy, use the public API
            # Get the distribution
            if isinstance(obs_tensor, dict):
                # MultiInputActorCriticPolicy path
                features = self.policy.extract_features(obs_tensor)
                latent_pi = self.policy.mlp_extractor.forward_actor(features)
                latent_vf = self.policy.mlp_extractor.forward_critic(features)
            else:
                # Standard ActorCriticPolicy path
                features = self.policy.extract_features(obs_tensor)
                latent_pi, latent_vf = self.policy.mlp_extractor(features)

            # Get action distribution from latent
            distribution = self.policy.action_net(latent_pi)

            # Get action probabilities
            if deterministic:
                action = torch.argmax(distribution, dim=-1)
            else:
                action = torch.distributions.Categorical(logits=distribution).sample()

            # Get full probability distribution
            all_probs = torch.softmax(distribution, dim=-1)

            # Get value estimate from latent
            value = self.policy.value_net(latent_vf)

        action_idx = int(action.cpu().numpy().flatten()[0])

        # Decode action (45 discrete actions: 9 directions × 5 intensities)
        direction_idx = action_idx // self.n_intensities
        intensity_idx = action_idx % self.n_intensities

        # Extract direction probabilities
        # Sum probabilities for all actions with each direction
        direction_probs = np.zeros(self.n_directions)
        for dir_idx in range(self.n_directions):
            start_idx = dir_idx * self.n_intensities
            end_idx = start_idx + self.n_intensities
            direction_probs[dir_idx] = all_probs[0, start_idx:end_idx].sum().item()

        # Extract intensity probabilities
        # Sum probabilities for all actions with each intensity
        intensity_probs = np.zeros(self.n_intensities)
        for int_idx in range(self.n_intensities):
            indices = [dir_idx * self.n_intensities + int_idx for dir_idx in range(self.n_directions)]
            intensity_probs[int_idx] = all_probs[0, indices].sum().item()

        # Flatten observation for visualization (simplified)
        if isinstance(observation, dict):
            # For dict observations, just use the global features
            raw_obs = observation.get('global', np.array([0.0])).tolist()
        else:
            raw_obs = observation.tolist() if observation.ndim == 1 else observation[0].tolist()

        details = {
            'direction_probs': direction_probs.tolist(),
            'intensity_probs': intensity_probs.tolist(),
            'build_prob': 0.0,  # Phase 3 doesn't have build action
            'selected_action': action_idx,
            'direction': self.direction_names[direction_idx],
            'intensity': self.intensity_values[intensity_idx],
            'build': False,  # Phase 3 doesn't have build action
            'value_estimate': float(value.cpu().numpy().flatten()[0]),
            'raw_observation': raw_obs,
        }

        # Try to extract attention weights if model uses attention
        try:
            attention_weights = self.extract_attention_weights(obs_tensor)
            if attention_weights is not None:
                details['attention_weights'] = attention_weights
        except Exception as e:
            # Model doesn't use attention, that's okay
            pass

        return action_idx, details

    def extract_attention_weights(self, obs_tensor: torch.Tensor) -> Optional[list]:
        """
        Extract attention weights from model if it uses attention mechanism
        Returns None if model doesn't use attention
        """
        # Check if policy has attention layers
        if not hasattr(self.policy, 'mlp_extractor'):
            return None

        mlp_extractor = self.policy.mlp_extractor

        # Look for attention layers in the model
        attention_weights = []
        for name, module in mlp_extractor.named_modules():
            if 'attention' in name.lower():
                # Try to get attention weights
                try:
                    if hasattr(module, 'attention_weights'):
                        weights = module.attention_weights
                        if weights is not None:
                            attention_weights.append(weights.cpu().numpy().tolist())
                except:
                    pass

        return attention_weights if attention_weights else None

    def get_action_explanation(self, action_idx: int) -> str:
        """Get human-readable explanation of an action"""
        direction_idx = action_idx // self.n_intensities
        intensity_idx = action_idx % self.n_intensities

        direction = self.direction_names[direction_idx]
        intensity = self.intensity_values[intensity_idx]

        explanation = f"{direction} @ {intensity*100:.0f}%"

        return explanation
