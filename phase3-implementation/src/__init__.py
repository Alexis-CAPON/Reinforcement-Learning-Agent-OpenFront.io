"""
OpenFront.io Phase 3 - Battle Royale RL Agent

This package contains the implementation of a reinforcement learning agent
for OpenFront.io battle royale mode using PPO with curriculum learning.
"""

__version__ = "3.0.0"
__author__ = "OpenFront.io RL Team"

from .environment import OpenFrontEnv
from .model import BattleRoyaleExtractor, BattleRoyalePolicy

__all__ = [
    'OpenFrontEnv',
    'BattleRoyaleExtractor',
    'BattleRoyalePolicy'
]
