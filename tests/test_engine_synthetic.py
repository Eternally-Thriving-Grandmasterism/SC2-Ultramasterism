"""Unit tests of the pure engine on synthetic event objects."""

import math
from types import SimpleNamespace

import pytest

from sc2um.engine import (
    LEGACY_FRAMES_PER_SECOND,
    LOTV_FRAMES_PER_SECOND,
    analyze_events,
    format_clock,
    per_minute,
)

FPS = LOTV_FRAMES_PER_SECOND


def at(seconds):
    """Frame number for a game-clock time in LotV."""
    return int(math.ceil(seconds * FPS - 1e-9))


def player(pid, name="P", race="Protoss", result="Win", team=1):
    return SimpleNamespace(pid=pid, name=name, play_race=race, result=result, team_id=team, is_human=True)


def unit(is_building=False, is_army=False, is_worker=False, owner_pid=None):
    owner = SimpleNamespace(pid=owner_pid) if owner_pid else None
    return SimpleNamespace(is_building=is_building, is_army=is_army, is_worker=is_worker, owner=owner)


def born(seconds, pid, name, **flags):
    return SimpleNamespace(name="UnitBornEvent", frame=at(seconds), control_pid=pid, unit_type_name=name, unit=unit(**flags))


def init(seconds, pid, name, building=True):
    return SimpleNamespace(name="UnitInitEvent", frame=at(seconds), control_pid=pid, unit_type_name=name, unit=unit(is_building=building))


def upgrade(seconds, pid, name):
    return SimpleNamespace(name="UpgradeCompleteEvent", frame=at(seconds), pid=pid, upgrade_type_name=name)


def morph(seconds, pid, name):
    return SimpleNamespace(name="UnitTypeChangeEvent", frame=at(seconds), unit_type_name=name, unit=unit(owner_pid=pid))


def stats(seconds, pid, workers, used, made, minerals=0, gas=0):
    return SimpleNamespace(
        name="PlayerStatsEvent",
        frame=at(seconds),
        pid=pid,
        workers_active_count=workers,
        food_used=used,
        food_made=made,
        minerals_used_active_forces=minerals,
        vespene_used_active_forces=gas,
    )


@pytest.mark.parametrize(
    "seconds,expected",
    [(0, "00:00"), (5, "00:05"), (59.9, "00:59"), (60, "01:00"), (754, "12:34"), (3600, "60:00"), (-3, "00:00")],
)
def test_format_clock(seconds, expected):
    assert format_clock(seconds) == expected


def test_build_order_kinds_times_and_supply():
    events = [
        stats(0, 1, 12, 12, 15),
        born(0, 1, "Probe", is_worker=True),  # starting worker, ignored
        born(12, 1, "Probe", is_worker=True),
        stats(14, 1, 13, 14, 15),
        init(18, 1, "Pylon"),
        init(40, 1, "Gateway"),
        upgrade(41, 1, "SprayProtoss"),  # cosmetic, ignored
        born(60, 1, "Larva"),  # ignored unit
        born(70, 1, "BeaconArmy"),  # no worker/army flag, ignored
        upgrade(200, 1, "WarpGateResearch"),
        born(210, 1, "Stalker", is_army=True),
    ]
    (report,) = analyze_events([player(1)], events, minutes=10)
    got = [(i.clock, i.name, i.kind, i.event, i.supply) for i in report.build_order]
    assert got == [
        ("00:12", "Probe", "unit", "completed", "12/15"),
        ("00:18", "Pylon", "structure", "started", "14/15"),
        ("00:40", "Gateway", "structure", "started", "14/15"),
        ("03:20", "WarpGateResearch", "upgrade", "completed", "14/15"),
        ("03:30", "Stalker", "unit", "completed", "14/15"),
    ]


def test_build_order_respects_minutes_limit():
    events = [init(30, 1, "Pylon"), init(119, 1, "Gateway"), init(121, 1, "Nexus")]
    (report,) = analyze_events([player(1)], events, minutes=2)
    assert [i.name for i in report.build_order] == ["Pylon", "Gateway"]


def test_supply_is_none_before_first_stats_sample():
    (report,) = analyze_events([player(1)], [init(5, 1, "Pylon")])
    assert report.build_order[0].supply is None


def test_tracked_morphs_use_unit_owner():
    events = [morph(100, 2, "Lair"), morph(110, 2, "Egg"), morph(120, 2, "Baneling")]
    (report,) = analyze_events([player(2, race="Zerg")], events)
    assert [(i.name, i.kind) for i in report.build_order] == [("Lair", "morph"), ("Baneling", "morph")]


def test_warp_in_is_reported_as_unit_started():
    (report,) = analyze_events([player(1)], [init(300, 1, "Zealot", building=False)])
    item = report.build_order[0]
    assert (item.kind, item.event) == ("unit", "started")


def test_workers_at_checkpoints_and_short_game():
    events = [
        stats(170, 1, 20, 22, 31),
        stats(180, 1, 22, 24, 31),
        stats(190, 1, 23, 25, 31),
        stats(355, 1, 40, 50, 62),
        stats(400, 1, 44, 60, 70),
    ]
    (report,) = analyze_events([player(1)], events, game_seconds=400)
    assert report.workers_at == {"3:00": 22, "6:00": 40, "10:00": None}


def test_custom_worker_checkpoints():
    events = [stats(60, 1, 15, 15, 23), stats(120, 1, 19, 20, 23)]
    (report,) = analyze_events([player(1)], events, worker_checkpoints=(1, 2), game_seconds=125)
    assert report.workers_at == {"1:00": 15, "2:00": 19}


def test_army_timeline_values():
    events = [stats(60, 1, 16, 18, 23, minerals=100, gas=0), stats(120, 1, 20, 30, 39, minerals=400, gas=150)]
    (report,) = analyze_events([player(1)], events)
    timeline = report.army_timeline
    assert [s.clock for s in timeline] == ["01:00", "02:00"]
    assert [s.army_value for s in timeline] == [100, 550]
    assert [s.army_supply for s in timeline] == [2.0, 10.0]


def test_per_minute_keeps_last_sample_each_minute():
    events = [stats(t, 1, 12, 12, 15) for t in (10, 50, 70, 119, 130)]
    (report,) = analyze_events([player(1)], events)
    assert [s.seconds for s in per_minute(report.army_timeline)] == pytest.approx([50, 119, 130], abs=0.05)


def test_team_game_events_are_split_by_player():
    players = [player(1, "A", team=1), player(2, "B", team=1), player(3, "C", team=2), player(4, "D", team=2)]
    events = [init(20 + pid, pid, "Pylon") for pid in (1, 2, 3, 4)] + [init(30, 9, "Pylon")]
    reports = analyze_events(players, events)
    assert [r.name for r in reports] == ["A", "B", "C", "D"]
    assert [r.team for r in reports] == [1, 1, 2, 2]
    assert all(len(r.build_order) == 1 for r in reports)


def test_missing_player_fields_do_not_crash():
    weird = SimpleNamespace(pid=5)
    (report,) = analyze_events([weird], [])
    assert (report.name, report.race, report.result) == ("Player 5", "Unknown", "Unknown")
    assert report.build_order == []
    assert report.workers_at == {"3:00": None, "6:00": None, "10:00": None}


def test_legacy_clock_rate():
    events = [SimpleNamespace(name="UnitInitEvent", frame=16 * 90, control_pid=1, unit_type_name="Barracks", unit=unit(is_building=True))]
    (report,) = analyze_events([player(1)], events, frames_per_clock_second=LEGACY_FRAMES_PER_SECOND)
    assert report.build_order[0].clock == "01:30"


def test_events_out_of_order_are_sorted():
    events = [init(40, 1, "Gateway"), init(18, 1, "Pylon")]
    (report,) = analyze_events([player(1)], events)
    assert [i.name for i in report.build_order] == ["Pylon", "Gateway"]
