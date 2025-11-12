# Reward Function & Training Strategy

## Reward Function

### Simple Reward Design

```python
def compute_reward(current_state, previous_state):
    reward = 0.0
    
    # 1. Territory change (primary objective)
    territory_change = current_state.territory_pct - previous_state.territory_pct
    reward += territory_change * 1000
    
    # 2. Population management (maintain 40-50% for optimal growth)
    pop_ratio = current_state.population / current_state.max_population
    if 0.40 <= pop_ratio <= 0.50:
        reward += 5  # In optimal range
    elif pop_ratio < 0.20:
        reward -= 10  # Too low, wasting growth
    elif pop_ratio > 0.80:
        reward -= 5  # Too high, slow growth
    
    # 3. Victory/Defeat (sparse)
    if current_state.territory_pct >= 0.80:
        reward += 10000  # Victory
    if current_state.territory_pct == 0.0:
        reward -= 10000  # Eliminated
    
    # 4. Survival bonus
    reward += 0.5  # Per timestep alive
    
    return reward
```

**That's it. 4 components.**

### Reward Breakdown

| Component | Weight | Purpose |
|-----------|--------|---------|
| Territory change | 1000× | Main objective |
| Population ratio | 5-10× | Core mechanic |
| Win/lose | 10000× | Sparse endpoint |
| Survival | 0.5× | Stay alive longer |

### Why This Works

- **Territory change**: Direct alignment with goal
- **Population management**: Teaches critical 40-50% sweet spot
- **Sparse rewards**: Clear success/failure signal
- **Survival bonus**: Encourages not dying early

**No complex tuning needed.**

## Training Strategy

### Curriculum Learning

**Phase 1: Learn Basics (100K steps, ~12 hours)**
```python
config = {
    'num_bots': 10,
    'game_duration': '10min',
    'map_size': 'medium'
}
```
**Goal**: Learn to expand, avoid elimination  
**Expected**: 5-10% win rate

**Phase 2: Handle Competition (300K steps, ~1.5 days)**
```python
config = {
    'num_bots': 25,
    'game_duration': '15min',
    'map_size': 'large'
}
```
**Goal**: Survive longer, opportunistic attacks  
**Expected**: 10-20% win rate

**Phase 3: Full Challenge (500K steps, ~2.5 days)**
```python
config = {
    'num_bots': 50,
    'game_duration': '20min',
    'map_size': 'large'
}
```
**Goal**: Consistent top 10 placement, occasional wins  
**Expected**: 20-30% win rate

### PPO Hyperparameters

```python
ppo_config = {
    # Learning
    'learning_rate': 3e-4,
    'n_steps': 1024,           # Rollout length
    'batch_size': 128,
    'n_epochs': 10,
    
    # PPO specific
    'gamma': 0.995,            # Discount factor (long episodes)
    'gae_lambda': 0.95,
    'clip_range': 0.2,
    
    # Regularization
    'ent_coef': 0.02,          # Exploration bonus
    'vf_coef': 0.5,            # Value loss weight
    'max_grad_norm': 0.5,
    
    # Environment
    'n_envs': 8,               # Parallel games
    
    # Device
    'device': 'mps',           # or 'cuda' or 'cpu'
}
```

### Training Timeline

```
Hardware: M4 Max or RTX 3060

Phase 1: Basics
├─ Steps: 100K
├─ Time: ~12 hours
└─ Outcome: Can expand, survive

Phase 2: Competition  
├─ Steps: 300K (total 400K)
├─ Time: ~1.5 days
└─ Outcome: Wins occasionally

Phase 3: Full Challenge
├─ Steps: 500K (total 900K)
├─ Time: ~2.5 days
└─ Outcome: 25-30% win rate

Total: 4-5 days
```

### Training Loop

```python
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv

# Create environments
env = SubprocVecEnv([
    make_env(num_bots=10) for _ in range(8)
])

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
    policy_kwargs={'features_extractor_class': BattleRoyaleExtractor},
    verbose=1,
    device='mps'
)

# Train
model.learn(total_timesteps=900_000)
model.save("openfront_agent")
```

## Evaluation

### Metrics to Track

```python
eval_metrics = {
    'win_rate': 0.0,              # % of games won
    'avg_rank': 0.0,              # Average placement
    'avg_territory': 0.0,         # Territory at end
    'survival_time': 0.0,         # How long alive
    'elimination_rate': 0.0       # % eliminated
}
```

### Evaluation Protocol

```python
def evaluate(model, n_episodes=50):
    results = []
    
    for _ in range(n_episodes):
        obs = eval_env.reset()
        done = False
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = eval_env.step(action)
        
        results.append({
            'won': info['territory_pct'] >= 0.80,
            'rank': info['final_rank'],
            'territory': info['territory_pct'],
            'survival': info['timesteps_alive']
        })
    
    return compute_metrics(results)
```

**Evaluate every 50K steps.**

## Common Issues

### Issue: Agent Dies Early

**Symptom**: Eliminated in first 5 minutes  
**Solution**: 
- Increase survival bonus (0.5 → 1.0)
- Lower starting bot count (50 → 25)
- Increase entropy (0.02 → 0.05)

### Issue: Agent Too Passive

**Symptom**: Doesn't attack, just waits  
**Solution**:
- Increase territory reward weight (1000 → 1500)
- Decrease survival bonus (0.5 → 0.2)
- Ensure action masking isn't too restrictive

### Issue: Population Mismanagement

**Symptom**: Always at 0% or 100% population  
**Solution**:
- Increase population reward (5 → 10)
- Add penalty for population crashes
- Check if agent sees population ratio in state

### Issue: Slow Convergence

**Symptom**: No improvement after 200K steps  
**Solution**:
- Increase learning rate (3e-4 → 5e-4)
- Increase parallel environments (8 → 16)
- Simplify curriculum (fewer bots initially)

## Optimization Tips

**Speed up training:**
```python
# More parallel environments
n_envs = 16  # Up from 8

# Shorter rollouts for faster updates
n_steps = 512  # Down from 1024

# Use GPU/MPS
device = 'mps'  # or 'cuda'
```

**Improve sample efficiency:**
```python
# More optimization per rollout
n_epochs = 15  # Up from 10

# Larger batch size
batch_size = 256  # Up from 128
```

**Better exploration:**
```python
# Higher entropy coefficient
ent_coef = 0.05  # Up from 0.02

# Vary bot count per episode
bot_counts = [10, 15, 20, 25, 30]
```

---

**Next**: [04_IMPLEMENTATION.md](04_IMPLEMENTATION.md)
