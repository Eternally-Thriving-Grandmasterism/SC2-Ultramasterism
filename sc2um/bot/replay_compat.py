"""Let sc2reader read replays saved through the StarCraft II API.

Replays saved by a game created through the API (as python-sc2 does)
have an empty ``cache_handles`` list in ``replay.details``. sc2reader
1.9.0 reads ``cache_handles[0]`` to get the region and uses the handle
hashes to detect the expansion, so it raises ``IndexError`` on them.

:func:`api_replay_support` patches sc2reader for the duration of a
``with`` block only: when ``cache_handles`` is empty it inserts one
placeholder handle (no region, the Legacy of the Void dependency hash),
which is what the Linux 4.x clients run. Normal replays are unaffected.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager

VOID_DEPENDENCY_HASH = hashlib.sha256(b"Standard Data: Void.SC2Mod").hexdigest()


class _PlaceholderHandle:
    server = ""
    hash = VOID_DEPENDENCY_HASH
    type = "s2ma"
    url = None

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<API replay placeholder cache handle>"


def fill_missing_cache_handles(raw_data: dict) -> bool:
    """Insert a placeholder handle if the details have none. Returns True if changed."""
    for key in ("replay.details", "replay.details.backup"):
        details = raw_data.get(key)
        if details is None:
            continue
        if not details.get("cache_handles"):
            details["cache_handles"] = [_PlaceholderHandle()]
            return True
        return False
    return False


@contextmanager
def api_replay_support():
    from sc2reader import resources

    original = resources.Replay.load_details

    def load_details(self):
        fill_missing_cache_handles(self.raw_data)
        return original(self)

    resources.Replay.load_details = load_details
    try:
        yield
    finally:
        resources.Replay.load_details = original


RESULTS = {1: "Win", 2: "Loss", 3: "Tie"}
HUMAN_CONTROL = 2  # slot controlled by a user (here: the API bot); 3 is built-in AI


class DetailsPlayer:
    """Minimal player built from ``replay.details`` (pid, name, race, result, team)."""

    def __init__(self, pid: int, raw: dict) -> None:
        self.pid = pid
        self.name = str(raw.get("name") or f"Player {pid}")
        self.play_race = raw.get("race") or "Unknown"
        self.result = RESULTS.get(raw.get("result"), "Unknown")
        team = raw.get("team")
        self.team_id = team + 1 if isinstance(team, int) else None
        self.is_human = raw.get("control") == HUMAN_CONTROL


def players_from_details(raw_data: dict) -> list:
    """Players from ``replay.details``, numbered 1..n like the tracker events."""
    details = raw_data.get("replay.details") or raw_data.get("replay.details.backup") or {}
    players = [p for p in details.get("players") or [] if not p.get("observe")]
    return [DetailsPlayer(index, raw) for index, raw in enumerate(players, start=1)]


class ReplayView:
    """Wraps an sc2reader replay, filling in players when sc2reader found none.

    API replays have no ``replay.attributes.events`` file, so sc2reader
    leaves ``replay.players`` empty; the names, races, results and teams
    are still in ``replay.details``.
    """

    def __init__(self, replay) -> None:
        self._replay = replay
        players = list(getattr(replay, "players", []) or [])
        self.players = players or players_from_details(getattr(replay, "raw_data", {}) or {})
        replay_type = getattr(replay, "type", None)
        if not replay_type and self.players:
            teams = {}
            for p in self.players:
                teams[p.team_id] = teams.get(p.team_id, 0) + 1
            replay_type = "v".join(str(teams[t]) for t in sorted(teams, key=str))
        self.type = replay_type

    def __getattr__(self, name):
        return getattr(self._replay, name)


def load_api_replay(path: str):
    """Load a replay saved through the API (works for normal replays too).

    Game events are skipped (load level 3): the replay engine only needs
    tracker events, and some API replays have command events without a
    player that break sc2reader's game-event plugins.
    """
    import sc2reader

    with api_replay_support():
        replay = sc2reader.load_replay(path, load_level=3)
    return ReplayView(replay)
