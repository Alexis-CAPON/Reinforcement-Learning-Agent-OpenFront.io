"""
Short training test to verify loss detection works during PPO training
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'rl_env'))

from openfrontio_env import OpenFrontIOEnv
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor
import logging

logging.basicConfig(level=logging.INFO)

print("Testing loss detection during PPO training...")
print("=" * 70)

# Create environment
def make_env():
    env = OpenFrontIOEnv()
    env = Monitor(env)
    return env

env = DummyVecEnv([make_env])

# Create simple PPO model
model = PPO(
    "MultiInputPolicy",
    env,
    learning_rate=0.0003,
    n_steps=512,  # Small rollout
    batch_size=64,
    verbose=1
)

print("\nTraining for 3000 timesteps (should see 1-2 episodes)...")
model.learn(total_timesteps=3000)

print("\n" + "=" * 70)
print("Training complete! Check the episode logs above.")
print("You should see:")
print("  - 'lost=True' when agent is eliminated")
print("  - 'terminated=True' (not truncated)")
print("  - Final tiles=0")
print("=" * 70)

env.close()
