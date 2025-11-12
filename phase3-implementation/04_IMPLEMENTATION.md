# Implementation Guide

## Project Structure

```
openfront-rl/
├── src/
│   ├── environment.py       # Gymnasium wrapper
│   ├── model.py             # Neural network
│   ├── train.py             # Training script
│   └── utils.py             # Helpers
├── configs/
│   └── config.yaml          # Hyperparameters
├── checkpoints/             # Saved models
└── requirements.txt
```

## Installation

```bash
pip install torch torchvision torchaudio
pip install stable-baselines3[extra]
pip install gymnasium
pip install numpy
```

## 1. Environment Wrapper

```python
# src/environment.py

import gymnasium as gym
from gymnasium import spaces
import numpy as np

class OpenFrontEnv(gym.Env):
    def __init__(self, game_interface, num_bots=50):
        super().__init__()
        
        self.game = game_interface
        self.num_bots = num_bots
        
        # Observation space
        self.observation_space = spaces.Dict({
            'map': spaces.Box(0, 1, (128, 128, 5), dtype=np.float32),
            'global': spaces.Box(-np.inf, np.inf, (16,), dtype=np.float32)
        })
        
        # Action space: 9 directions × 5 intensities × 2 build = 90
        self.action_space = spaces.Discrete(90)
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.game.start_new_game(num_bots=self.num_bots)
        self.previous_state = None
        return self._get_obs(), {}
    
    def step(self, action):
        # Decode action
        direction = action // 10
        intensity_idx = (action % 10) // 2
        build = action % 2
        
        # Execute
        self._execute_action(direction, intensity_idx, build)
        self.game.update()
        
        # Get results
        obs = self._get_obs()
        reward = self._compute_reward()
        terminated = self._check_done()
        
        self.previous_state = self.game.get_state()
        return obs, reward, terminated, False, {}
    
    def _get_obs(self):
        state = self.game.get_state()
        return {
            'map': self._extract_map(state),
            'global': self._extract_global(state)
        }
    
    def _extract_map(self, state):
        # Downsample 512×512 to 128×128
        map_feat = np.zeros((128, 128, 5), dtype=np.float32)
        
        # Your territory
        map_feat[:,:,0] = self._downsample(state.your_territory_mask)
        
        # Enemy density (aggregate all opponents)
        map_feat[:,:,1] = self._downsample(state.enemy_count_map / 50)
        
        # Neutral territory
        map_feat[:,:,2] = self._downsample(state.neutral_mask)
        
        # Your troops
        map_feat[:,:,3] = self._downsample(state.your_troops / 10000)
        
        # Enemy troops (aggregated)
        map_feat[:,:,4] = self._downsample(state.enemy_troops / 10000)
        
        return map_feat
    
    def _downsample(self, array_512):
        # Simple 4×4 average pooling: 512→128
        return array_512.reshape(128, 4, 128, 4).mean(axis=(1, 3))
    
    def _extract_global(self, state):
        return np.array([
            state.population / state.max_population,
            state.max_population / 100000,
            state.population_growth_rate,
            state.territory_pct,
            state.territory_change,
            state.rank / 50,
            state.border_pressure / 10,
            state.num_cities,
            state.gold / 50000,
            state.time_alive / state.max_time,
            state.game_progress,
            state.nearest_threat / 128,
            0, 0, 0, 0  # Padding
        ], dtype=np.float32)
    
    def _execute_action(self, direction, intensity_idx, build):
        intensities = [0.20, 0.35, 0.50, 0.75, 1.00]
        
        # Attack in direction
        if direction < 8:
            target = self._find_target_in_direction(direction)
            if target:
                troops = int(self.game.population * intensities[intensity_idx])
                self.game.attack(target, troops)
        
        # Build city
        if build == 1 and self.game.gold >= 5000:
            location = self._find_safe_location()
            if location:
                self.game.build_city(location)
    
    def _compute_reward(self):
        state = self.game.get_state()
        prev = self.previous_state
        
        if prev is None:
            return 0.5
        
        reward = 0.0
        
        # Territory change
        reward += (state.territory_pct - prev.territory_pct) * 1000
        
        # Population management
        pop_ratio = state.population / state.max_population
        if 0.40 <= pop_ratio <= 0.50:
            reward += 5
        elif pop_ratio < 0.20:
            reward -= 10
        
        # Win/lose
        if state.territory_pct >= 0.80:
            reward += 10000
        if state.territory_pct == 0:
            reward -= 10000
        
        # Survival
        reward += 0.5
        
        return reward
    
    def _check_done(self):
        state = self.game.get_state()
        return state.territory_pct >= 0.80 or state.territory_pct == 0
```

## 2. Neural Network

```python
# src/model.py

import torch
import torch.nn as nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class BattleRoyaleExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=256):
        super().__init__(observation_space, features_dim)
        
        # CNN for map
        self.cnn = nn.Sequential(
            nn.Conv2d(5, 32, kernel_size=8, stride=4, padding=2),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=0),
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
            nn.Linear(640, features_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )
    
    def forward(self, observations):
        # Process map
        map_features = self.cnn(observations['map'])
        
        # Process global
        global_features = self.mlp(observations['global'])
        
        # Combine
        combined = torch.cat([map_features, global_features], dim=1)
        return self.fusion(combined)
```

## 3. Training Script

```python
# src/train.py

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from src.environment import OpenFrontEnv
from src.model import BattleRoyaleExtractor

def make_env(num_bots):
    def _init():
        game = OpenFrontGame()  # Your game interface
        return OpenFrontEnv(game, num_bots=num_bots)
    return _init

def train():
    # Create parallel environments
    env = SubprocVecEnv([make_env(num_bots=10) for _ in range(8)])
    
    # Create model
    model = PPO(
        policy="MultiInputPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=1024,
        batch_size=128,
        n_epochs=10,
        gamma=0.995,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.02,
        vf_coef=0.5,
        max_grad_norm=0.5,
        policy_kwargs={
            'features_extractor_class': BattleRoyaleExtractor,
            'features_extractor_kwargs': {'features_dim': 256}
        },
        verbose=1,
        device='mps',  # or 'cuda' or 'cpu'
        tensorboard_log="./logs/"
    )
    
    # Callbacks
    checkpoint = CheckpointCallback(
        save_freq=50_000,
        save_path='./checkpoints/',
        name_prefix='openfront'
    )
    
    # Train
    model.learn(
        total_timesteps=900_000,
        callback=checkpoint,
        progress_bar=True
    )
    
    model.save("openfront_final")
    env.close()

if __name__ == "__main__":
    train()
```

## 4. Evaluation Script

```python
# src/evaluate.py

from stable_baselines3 import PPO
from src.environment import OpenFrontEnv

def evaluate(model_path, n_episodes=50):
    model = PPO.load(model_path)
    env = OpenFrontEnv(OpenFrontGame(), num_bots=50)
    
    results = []
    for episode in range(n_episodes):
        obs, _ = env.reset()
        done = False
        episode_reward = 0
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, _, info = env.step(action)
            episode_reward += reward
        
        results.append({
            'reward': episode_reward,
            'territory': info['territory_pct'],
            'won': info['territory_pct'] >= 0.80
        })
        
        print(f"Episode {episode+1}: Territory={info['territory_pct']:.2%}, "
              f"Won={info['territory_pct'] >= 0.80}")
    
    win_rate = sum(r['won'] for r in results) / n_episodes
    avg_territory = sum(r['territory'] for r in results) / n_episodes
    
    print(f"\nResults over {n_episodes} episodes:")
    print(f"Win rate: {win_rate:.2%}")
    print(f"Avg territory: {avg_territory:.2%}")
    
    env.close()

if __name__ == "__main__":
    evaluate("openfront_final.zip", n_episodes=50)
```

## 5. Quick Test

Before full training, test everything works:

```python
# test.py

from src.environment import OpenFrontEnv
import numpy as np

# Test environment
env = OpenFrontEnv(game_interface, num_bots=10)
obs, _ = env.reset()

print("Observation shapes:")
print(f"  Map: {obs['map'].shape}")
print(f"  Global: {obs['global'].shape}")

# Test random actions
for i in range(10):
    action = env.action_space.sample()
    obs, reward, done, _, info = env.step(action)
    print(f"Step {i}: reward={reward:.2f}, done={done}")
    
    if done:
        obs, _ = env.reset()

env.close()
print("Environment test passed!")
```

## 6. Run Training

```bash
# Start training
python src/train.py

# Monitor with tensorboard
tensorboard --logdir ./logs/

# Evaluate after training
python src/evaluate.py
```

## 7. Configuration File

```yaml
# configs/config.yaml

training:
  total_timesteps: 900000
  n_envs: 8
  
ppo:
  learning_rate: 3.0e-4
  n_steps: 1024
  batch_size: 128
  n_epochs: 10
  gamma: 0.995
  gae_lambda: 0.95
  clip_range: 0.2
  ent_coef: 0.02
  vf_coef: 0.5
  max_grad_norm: 0.5

curriculum:
  phase1:
    num_bots: 10
    steps: 100000
  phase2:
    num_bots: 25
    steps: 300000
  phase3:
    num_bots: 50
    steps: 500000
```

## Common Issues

**Issue: "MPS not available"**
```python
# Solution: Use CPU or CUDA
device = 'cpu'  # or 'cuda' if NVIDIA GPU
```

**Issue: Out of memory**
```python
# Solution: Reduce parallel envs or batch size
n_envs = 4      # Down from 8
batch_size = 64  # Down from 128
```

**Issue: Training too slow**
```python
# Solution: Use SubprocVecEnv for parallelization
from stable_baselines3.common.vec_env import SubprocVecEnv
env = SubprocVecEnv([make_env() for _ in range(n_envs)])
```

**Issue: Agent not learning**
```python
# Solution: Check observation normalization
print("Map range:", obs['map'].min(), obs['map'].max())  # Should be [0, 1]
print("Global range:", obs['global'].min(), obs['global'].max())  # Reasonable values
```

## Debugging Checklist

- [ ] Environment resets correctly
- [ ] Observations are normalized [0, 1]
- [ ] Actions execute as expected
- [ ] Rewards are reasonable magnitude (-100 to +100 typically)
- [ ] Model can do forward pass
- [ ] Training loop runs without errors
- [ ] Tensorboard shows metrics updating
- [ ] Checkpoints are being saved

## Expected Training Output

```
-----------------------------------------
| rollout/                |             |
|    ep_len_mean          | 245         |
|    ep_rew_mean          | 123.4       |
| time/                   |             |
|    fps                  | 120         |
|    iterations           | 100         |
|    time_elapsed         | 853         |
|    total_timesteps      | 102400      |
| train/                  |             |
|    entropy_loss         | -2.89       |
|    policy_loss          | -0.0156     |
|    value_loss           | 45.2        |
-----------------------------------------
```

---

That's it. Simple, focused, gets the job done.
