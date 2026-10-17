"""Loading replays with sc2reader and turning them into reports."""

from __future__ import annotations

import os
from typing import Optional

from sc2um.engine import (
    DEFAULT_WORKER_CHECKPOINTS,
    LEGACY_FRAMES_PER_SECOND,
    LOTV_FRAMES_PER_SECOND,
    analyze_events,
)

LOTV_CLOCK_MIN_BUILD = 34784


class ReplayError(Exception):
    """Raised when a replay cannot be read."""


def load_replay(path: str):
    """Load a ``.SC2Replay`` file with sc2reader (tracker events included)."""
    import sc2reader

    if not os.path.isfile(path):
        raise ReplayError(f"Replay not found: {path}")
    try:
        return sc2reader.load_replay(path, load_level=4)
    except Exception as exc:  # sc2reader raises many different errors
        raise ReplayError(f"Could not read replay {path}: {exc}") from exc


def frames_per_clock_second(replay) -> float:
    """Frames per second shown on the in-game clock for this replay.

    From patch 3.0 (build 34784, the same threshold sc2reader uses for
    ``game_length``) the clock shows real time on Faster speed, i.e.
    16 * 1.4 = 22.4 frames per second. Older replays use 16.
    """
    build = getattr(replay, "build", None) or 0
    if build >= LOTV_CLOCK_MIN_BUILD:
        return LOTV_FRAMES_PER_SECOND
    return LEGACY_FRAMES_PER_SECOND


def _game_seconds(replay, fps: float) -> Optional[float]:
    frames = getattr(replay, "frames", None)
    if frames:
        return frames / fps
    return None


def analyze_replay(
    replay_or_path,
    minutes: float = 10,
    worker_checkpoints=DEFAULT_WORKER_CHECKPOINTS,
) -> dict:
    """Analyze a replay (a path or an already loaded sc2reader replay).

    Returns a plain dict that can be serialised to JSON.
    """
    if isinstance(replay_or_path, (str, os.PathLike)):
        replay = load_replay(os.fspath(replay_or_path))
    else:
        replay = replay_or_path

    fps = frames_per_clock_second(replay)
    game_seconds = _game_seconds(replay, fps)
    players = list(getattr(replay, "players", []) or [])
    events = list(getattr(replay, "tracker_events", []) or [])
    reports = analyze_events(
        players,
        events,
        minutes=minutes,
        frames_per_clock_second=fps,
        game_seconds=game_seconds,
        worker_checkpoints=worker_checkpoints,
    )

    length = getattr(replay, "game_length", None)
    notes = []
    if not events:
        notes.append(
            "Replay has no tracker events (replays before patch 2.0.8 and "
            "some stripped replays lack them); build order, workers and "
            "army data are unavailable."
        )
    return {
        "file": getattr(replay, "filename", None),
        "map": getattr(replay, "map_name", None),
        "type": getattr(replay, "type", None),
        "category": getattr(replay, "category", None),
        "release": getattr(replay, "release_string", None),
        "expansion": getattr(replay, "expansion", None),
        "speed": getattr(replay, "speed", None),
        "length": str(length) if length is not None else None,
        "length_seconds": round(game_seconds, 2) if game_seconds is not None else None,
        "minutes_analyzed": minutes,
        "notes": notes,
        "players": [report.to_dict() for report in reports],
    }
