"""Pure analysis logic over sc2reader tracker events.

Nothing in this module opens files or imports sc2reader, so it can be
tested with small synthetic event objects. Events are read by duck
typing: each event needs a ``name`` (or a class name) such as
``"UnitBornEvent"`` plus the attributes sc2reader puts on that event.

Timing: sc2reader reports ``frame`` numbers at 16 frames per game
second. The in-game clock of Legacy of the Void (patch 3.0 onward) on
Faster speed runs 1.4x faster, i.e. 22.4 frames per displayed second.
Callers pass the right ``frames_per_clock_second`` for the replay.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Iterable, Optional

LOTV_FRAMES_PER_SECOND = 22.4
LEGACY_FRAMES_PER_SECOND = 16.0

DEFAULT_WORKER_CHECKPOINTS = (3, 6, 10)

WORKER_NAMES = frozenset({"SCV", "Probe", "Drone"})

# Units that are spawned by abilities or are cosmetic, not produced
# as part of a build order.
IGNORED_UNIT_NAMES = frozenset(
    {
        "Larva",
        "Egg",
        "Broodling",
        "BroodlingEscort",
        "Interceptor",
        "LocustMP",
        "LocustMPFlying",
        "AdeptPhaseShift",
        "MULE",
        "KD8Charge",
        "AutoTurret",
        "PointDefenseDrone",
        "Changeling",
        "ChangelingMarine",
        "ChangelingMarineShield",
        "ChangelingZealot",
        "ChangelingZergling",
        "ChangelingZerglingWings",
        "CreepTumor",
        "CreepTumorBurrowed",
        "CreepTumorQueen",
        "ParasiticBombDummy",
        "InvisibleTargetDummy",
        "DisruptorPhased",
        "ForceField",
    }
)

# Morphs recorded through UnitTypeChangeEvent that belong in a build order.
TRACKED_MORPHS = frozenset(
    {
        "Lair",
        "Hive",
        "GreaterSpire",
        "OrbitalCommand",
        "PlanetaryFortress",
        "Baneling",
        "Ravager",
        "Lurker",
        "LurkerMP",
        "BroodLord",
        "Overseer",
    }
)

IGNORED_UPGRADE_PREFIXES = ("Spray", "Reward", "GameHeart")


def format_clock(seconds: float) -> str:
    """Format a number of seconds as ``mm:ss`` (minutes may exceed 59)."""
    total = int(seconds)
    if total < 0:
        total = 0
    return f"{total // 60:02d}:{total % 60:02d}"


def _event_name(event) -> str:
    return getattr(event, "name", None) or type(event).__name__


def _event_pid(event) -> Optional[int]:
    """Player id that owns the thing an event describes."""
    for attr in ("control_pid", "pid"):
        value = getattr(event, attr, None)
        if value:
            return value
    unit = getattr(event, "unit", None)
    owner = getattr(unit, "owner", None)
    pid = getattr(owner, "pid", None)
    return pid or None


def _unit_flag(event, flag: str) -> bool:
    unit = getattr(event, "unit", None)
    return bool(getattr(unit, flag, False))


@dataclass
class BuildItem:
    clock: str
    seconds: float
    name: str
    kind: str  # "unit", "structure", "morph" or "upgrade"
    event: str  # "started" or "completed"
    supply: Optional[str] = None


@dataclass
class StatsSample:
    seconds: float
    clock: str
    workers: int
    supply_used: float
    supply_made: float
    army_supply: float
    army_value: int


@dataclass
class PlayerReport:
    pid: int
    name: str
    race: str
    result: str
    team: Optional[int] = None
    is_human: Optional[bool] = None
    build_order: list = field(default_factory=list)
    workers_at: dict = field(default_factory=dict)
    army_timeline: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _supply_at(samples: list, seconds: float) -> Optional[str]:
    latest = None
    for sample in samples:
        if sample.seconds <= seconds:
            latest = sample
        else:
            break
    if latest is None:
        return None
    return f"{int(latest.supply_used)}/{int(latest.supply_made)}"


def _latest_sample(samples: list, seconds: float) -> Optional[StatsSample]:
    latest = None
    for sample in samples:
        if sample.seconds <= seconds:
            latest = sample
        else:
            break
    return latest


def _stats_sample(event, fps: float) -> StatsSample:
    seconds = event.frame / fps
    workers = int(getattr(event, "workers_active_count", 0) or 0)
    used = float(getattr(event, "food_used", 0) or 0)
    made = float(getattr(event, "food_made", 0) or 0)
    minerals = int(getattr(event, "minerals_used_active_forces", 0) or 0)
    gas = int(getattr(event, "vespene_used_active_forces", 0) or 0)
    return StatsSample(
        seconds=round(seconds, 2),
        clock=format_clock(seconds),
        workers=workers,
        supply_used=used,
        supply_made=made,
        army_supply=max(used - workers, 0.0),
        army_value=minerals + gas,
    )


def _build_item(event, fps: float) -> Optional[tuple]:
    """Return ``(pid, BuildItem)`` for an event that belongs in a build order."""
    name = _event_name(event)
    frame = getattr(event, "frame", 0) or 0
    seconds = frame / fps

    if name == "UpgradeCompleteEvent":
        upgrade = getattr(event, "upgrade_type_name", "") or ""
        if not upgrade or upgrade.startswith(IGNORED_UPGRADE_PREFIXES):
            return None
        return _event_pid(event), BuildItem(
            format_clock(seconds), round(seconds, 2), upgrade, "upgrade", "completed"
        )

    unit_name = getattr(event, "unit_type_name", "") or ""
    if not unit_name or unit_name in IGNORED_UNIT_NAMES:
        return None

    if name == "UnitInitEvent":
        # Structures (and warp-ins) appear when they are started.
        kind = "structure" if _unit_flag(event, "is_building") else "unit"
        return _event_pid(event), BuildItem(
            format_clock(seconds), round(seconds, 2), unit_name, kind, "started"
        )

    if name == "UnitBornEvent":
        # Frame 0 holds the starting workers and town hall.
        if frame <= 0:
            return None
        is_worker = unit_name in WORKER_NAMES or _unit_flag(event, "is_worker")
        is_army = _unit_flag(event, "is_army")
        if not (is_worker or is_army):
            return None
        # Units are only recorded by the tracker when they finish.
        return _event_pid(event), BuildItem(
            format_clock(seconds), round(seconds, 2), unit_name, "unit", "completed"
        )

    if name == "UnitTypeChangeEvent":
        if unit_name not in TRACKED_MORPHS:
            return None
        return _event_pid(event), BuildItem(
            format_clock(seconds), round(seconds, 2), unit_name, "morph", "completed"
        )

    return None


def analyze_events(
    players: Iterable,
    events: Iterable,
    *,
    minutes: float = 10,
    frames_per_clock_second: float = LOTV_FRAMES_PER_SECOND,
    game_seconds: Optional[float] = None,
    worker_checkpoints: Iterable[int] = DEFAULT_WORKER_CHECKPOINTS,
) -> list:
    """Build one :class:`PlayerReport` per player.

    ``players`` are objects with ``pid``, ``name``, ``play_race`` and
    ``result`` (``team_id`` and ``is_human`` are optional). ``events``
    are tracker events. ``minutes`` limits the build order. Worker counts
    at a checkpoint are ``None`` when the game ended before it.
    """
    fps = float(frames_per_clock_second)
    limit = float(minutes) * 60.0
    reports = {}
    order = []
    for player in players:
        pid = getattr(player, "pid", None)
        if pid is None or pid in reports:
            continue
        reports[pid] = PlayerReport(
            pid=pid,
            name=str(getattr(player, "name", "") or f"Player {pid}"),
            race=str(getattr(player, "play_race", None) or getattr(player, "pick_race", None) or "Unknown"),
            result=str(getattr(player, "result", None) or "Unknown"),
            team=getattr(player, "team_id", None),
            is_human=getattr(player, "is_human", None),
        )
        order.append(pid)

    samples = {pid: [] for pid in reports}
    items = {pid: [] for pid in reports}
    last_frame = 0

    events = sorted(events, key=lambda e: getattr(e, "frame", 0) or 0)
    for event in events:
        frame = getattr(event, "frame", 0) or 0
        last_frame = max(last_frame, frame)
        if _event_name(event) == "PlayerStatsEvent":
            pid = _event_pid(event)
            if pid in samples:
                samples[pid].append(_stats_sample(event, fps))
            continue
        found = _build_item(event, fps)
        if found is None:
            continue
        pid, item = found
        if pid in items and item.seconds <= limit:
            items[pid].append(item)

    if game_seconds is None:
        game_seconds = last_frame / fps

    for pid in order:
        report = reports[pid]
        player_samples = samples[pid]
        for item in items[pid]:
            item.supply = _supply_at(player_samples, item.seconds)
        report.build_order = items[pid]
        for minute in worker_checkpoints:
            key = f"{int(minute)}:00"
            checkpoint = minute * 60.0
            sample = _latest_sample(player_samples, checkpoint)
            if game_seconds < checkpoint or sample is None:
                report.workers_at[key] = None
            else:
                report.workers_at[key] = sample.workers
        report.army_timeline = player_samples
    return [reports[pid] for pid in order]


def per_minute(timeline: list) -> list:
    """Reduce a stats timeline to the last sample of each whole minute."""
    picked = {}
    for sample in timeline:
        minute = int(sample.seconds // 60) if not isinstance(sample, dict) else int(sample["seconds"] // 60)
        picked[minute] = sample
    return [picked[m] for m in sorted(picked)]
