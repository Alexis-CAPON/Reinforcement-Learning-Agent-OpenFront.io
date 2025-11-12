# Network Architecture

## Overview

Simple CNN-based policy for battle royale gameplay.

**Total parameters**: ~500K  
**Memory**: 2-3 GB  
**Inference**: 10ms per decision

## Architecture Diagram

```
Map [128×128×5]           Global [16]
       ↓                        ↓
    CNN Branch              MLP Branch
       ↓                        ↓
   [512 features]          [128 features]
       └──────────┬──────────────┘
                  ↓
             Concatenate
                  ↓
             [640 features]
                  ↓
             Fusion MLP
                  ↓
             [256 features]
           ┌──────┴──────┐
           ↓             ↓
      Actor Head    Critic Head
           ↓             ↓
     Actions [90]   Value [1]
```

## Components

### 1. CNN Branch (Map Processing)

```python
nn.Sequential(
    # Conv1: 128×128×5 → 32×32×32
    nn.Conv2d(5, 32, kernel_size=8, stride=4, padding=2),
    nn.ReLU(),
    
    # Conv2: 32×32×32 → 16×16×64
    nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
    nn.ReLU(),
    
    # Conv3: 16×16×64 → 14×14×64
    nn.Conv2d(64, 64, kernel_size=3, stride=1, padding=0),
    nn.ReLU(),
    
    # Flatten: 14×14×64 = 12,544
    nn.Flatten(),
    
    # FC: 12,544 → 512
    nn.Linear(12544, 512),
    nn.ReLU()
)
```

**Purpose**: Extract spatial features (threats, opportunities, borders)

### 2. MLP Branch (Global Features)

```python
nn.Sequential(
    nn.Linear(16, 128),
    nn.ReLU(),
    nn.Linear(128, 128),
    nn.ReLU()
)
```

**Purpose**: Process your state (population, territory, rank, etc.)

### 3. Feature Fusion

```python
nn.Sequential(
    nn.Linear(640, 256),  # 512 + 128 = 640
    nn.ReLU(),
    nn.Dropout(0.1)
)
```

**Purpose**: Combine spatial and global information

### 4. Actor Head (Policy)

```python
nn.Sequential(
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Linear(128, 90)  # 9 directions × 5 intensities + 2 build
)
```

**Outputs**:
- Direction logits [9]: N, NE, E, SE, S, SW, W, NW, Wait
- Intensity logits [5]: 20%, 35%, 50%, 75%, 100%
- Build logits [2]: No, Yes

**Sampling**:
```python
direction = Categorical(logits=direction_logits).sample()
intensity = Categorical(logits=intensity_logits).sample()
build = Categorical(logits=build_logits).sample()
```

### 5. Critic Head (Value Function)

```python
nn.Sequential(
    nn.Linear(256, 128),
    nn.ReLU(),
    nn.Linear(128, 1)
)
```

**Output**: Estimated value of current state V(s)

## Complete Model

```python
class BattleRoyalePolicy(nn.Module):
    def __init__(self):
        super().__init__()
        
        # CNN for map
        self.cnn = nn.Sequential(
            nn.Conv2d(5, 32, 8, 4, 2), nn.ReLU(),
            nn.Conv2d(32, 64, 4, 2, 1), nn.ReLU(),
            nn.Conv2d(64, 64, 3, 1, 0), nn.ReLU(),
            nn.Flatten(),
            nn.Linear(12544, 512), nn.ReLU()
        )
        
        # MLP for global
        self.mlp = nn.Sequential(
            nn.Linear(16, 128), nn.ReLU(),
            nn.Linear(128, 128), nn.ReLU()
        )
        
        # Fusion
        self.fusion = nn.Sequential(
            nn.Linear(640, 256), nn.ReLU(), nn.Dropout(0.1)
        )
        
        # Heads
        self.actor = nn.Sequential(
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, 90)
        )
        self.critic = nn.Sequential(
            nn.Linear(256, 128), nn.ReLU(),
            nn.Linear(128, 1)
        )
    
    def forward(self, obs):
        map_feat = self.cnn(obs['map'])
        global_feat = self.mlp(obs['global'])
        combined = torch.cat([map_feat, global_feat], dim=1)
        shared = self.fusion(combined)
        
        action_logits = self.actor(shared)
        value = self.critic(shared)
        
        return action_logits, value
```

## Parameter Count

| Component | Parameters |
|-----------|-----------|
| CNN layers | ~410K |
| MLP branch | ~20K |
| Fusion | ~165K |
| Actor head | ~45K |
| Critic head | ~33K |
| **Total** | **~500K** |

## Design Rationale

**Why this architecture?**
- **Simple CNN**: 3 conv layers enough for spatial patterns
- **No ResNet**: Overkill for this game
- **No Attention**: 50+ opponents, aggregate instead
- **Small model**: Fast training and inference
- **Standard PPO**: Actor-critic with shared representation

**What it learns:**
- Where enemies are concentrated (avoid or exploit)
- Where neutral territory is (expand)
- Border pressure (defend or retreat)
- Population timing (when to attack vs grow)
- City placement (safe interior locations)

---

**Next**: [02_STATE_ACTIONS.md](02_STATE_ACTIONS.md)
