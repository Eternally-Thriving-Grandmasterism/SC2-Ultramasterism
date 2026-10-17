"""sc2um: a small StarCraft II replay engine built on sc2reader.

It reads a ``.SC2Replay`` file and extracts, per player, the race, the
result, an early build order, worker counts at fixed times and an army
timeline. It does not play the game.
"""

from sc2um.engine import (
    DEFAULT_WORKER_CHECKPOINTS,
    analyze_events,
    format_clock,
)
from sc2um.replay import analyze_replay, load_replay

__all__ = [
    "DEFAULT_WORKER_CHECKPOINTS",
    "analyze_events",
    "analyze_replay",
    "format_clock",
    "load_replay",
]

__version__ = "0.1.0"
