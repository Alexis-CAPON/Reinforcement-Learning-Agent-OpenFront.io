"""
Simple Reward Version - Let Agent Discover Strategy

Replace complex 15-component rewards with minimal survival-based rewards.
Philosophy: Tell agent WHAT to achieve (survive, hold territory), not HOW.
"""

# SIMPLE REWARD VERSION - Option 3: Survival + Territory + Terminal

def _compute_reward_simple(self):
    """
    Minimal reward structure - let agent discover consolidation naturally.

    Components:
    1. Survival: +1 per step
    2. Territory holding: +territory% × 10 per step
    3. Terminal: ±10000

    Total: 3 components (down from 15!)
    """
    if self.game is None or self.previous_state is None:
        return 0.1

    state = self._get_game_state()
    reward = 0.0

    # 1. SURVIVAL (base reward for staying alive)
    reward += 1.0

    # 2. TERRITORY HOLDING (reward proportional to territory controlled)
    #    This incentivizes both expansion AND holding
    if hasattr(state, 'territory_pct'):
        territory_reward = state.territory_pct * 10.0
        reward += territory_reward
        # Examples:
        # 10% territory: +1.0/step
        # 40% territory: +4.0/step
        # 50% territory: +5.0/step

    # 3. TERMINAL REWARDS (winning is everything!)
    if hasattr(state, 'territory_pct'):
        if state.territory_pct >= 0.80:
            # Victory!
            reward += 10000
        elif state.territory_pct == 0.0:
            # Eliminated
            reward += -10000

    # 4. TIMEOUT PENALTY (prevent infinite stalling)
    if self.step_count >= 10000:
        reward += -5000

    return reward


# EVEN SIMPLER - Option 1: Pure Survival + Terminal

def _compute_reward_minimal(self):
    """
    Absolute minimal rewards - pure survival signal.

    Agent must discover EVERYTHING on its own:
    - When to expand
    - When to consolidate
    - Optimal troop density
    - Multi-front management
    """
    if self.game is None:
        return 0.1

    state = self._get_game_state()
    reward = 0.0

    # 1. SURVIVAL
    reward += 1.0  # +1 per step alive

    # 2. TERMINAL ONLY
    if hasattr(state, 'territory_pct'):
        if state.territory_pct >= 0.80:
            reward += 10000  # Win
        elif state.territory_pct == 0.0:
            reward += -10000  # Lose

    return reward


# MIDDLE GROUND - Option 2: Survival + Rank

def _compute_reward_rank_based(self):
    """
    Rank-based survival - rewards staying competitive.

    Better rank = more reward per step.
    Natural pressure to both expand AND survive.
    """
    if self.game is None or self.previous_state is None:
        return 0.1

    state = self._get_game_state()
    reward = 0.0

    # 1. BASE SURVIVAL
    reward += 1.0

    # 2. RANK BONUS (better rank = more reward)
    if hasattr(state, 'rank') and hasattr(state, 'total_players'):
        if state.total_players > 0:
            rank_percentile = 1.0 - (state.rank / state.total_players)
            rank_bonus = rank_percentile * 2.0
            reward += rank_bonus
            # Rank 1/6: +1.67/step (83rd percentile)
            # Rank 2/6: +1.33/step
            # Rank 3/6: +0.67/step
            # Rank 6/6: +0.00/step (eliminated)

    # 3. TERMINAL
    if hasattr(state, 'territory_pct'):
        if state.territory_pct >= 0.80:
            reward += 10000
        elif state.territory_pct == 0.0:
            # Softer death penalty if survived long
            survival_credit = min(self.step_count * 1.0, 5000)
            reward += -10000 + survival_credit

    return reward


# COMPARISON TABLE

"""
Reward Complexity Comparison:

OLD (Complex - 15 components):
├── Territory change (±2)
├── Action bonus (+0.1)
├── Density rewards (+5/-10)
├── Overextension penalty (-666)
├── Troop loss penalty (-4)
├── Enemy kills (+5000)
├── Military strength (+1)
├── Focus/multi-front (±2)
├── Survival (+0.1/1000)
├── Rank improvement (+100)
├── Rank defense (±10)
├── Defensive wait (+1)
├── Territory milestones (+10)
├── Time penalty (-0.05)
└── Terminal (±10000)
Total: 15 conflicting signals!
Result: +14,761 reward, 0% wins

NEW (Simple - 3 components):
├── Survival (+1)
├── Territory holding (+territory% × 10)
└── Terminal (±10000)
Total: 3 clear signals
Expected: Reward correlates with winning


PHILOSOPHY SHIFT:

Before: "Micromanage every strategic decision"
After:  "Reward the objective, let agent discover strategy"

Before: "Don't overextend, consolidate here, focus attacks..."
After:  "Stay alive with lots of territory"

Before: Agent optimizes complex reward function (not winning)
After:  Agent optimizes survival (which requires winning strategy)
"""


# USAGE:

"""
To switch to simple rewards:

1. Backup current environment.py:
   cp src/environment.py src/environment_complex_rewards.py

2. Replace _compute_reward() in environment.py with one of:
   - _compute_reward_simple()     [Recommended]
   - _compute_reward_minimal()    [Most extreme]
   - _compute_reward_rank_based() [Middle ground]

3. Train and compare:
   python src/train_attention.py \\
     --device mps \\
     --n-envs 12 \\
     --total-timesteps 500000 \\
     --no-curriculum \\
     --num-bots 5

4. Check if win rate improves (currently 0%)
"""
