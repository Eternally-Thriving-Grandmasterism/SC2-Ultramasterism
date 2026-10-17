"""The replay engine on a replay saved through the StarCraft II API (no game needed)."""

import base64
from pathlib import Path

import pytest

from sc2um import analyze_replay
from sc2um.bot import replay_compat
from sc2um.bot.runner import replay_summary

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(scope="module")
def api_replay(tmp_path_factory):
    out = tmp_path_factory.mktemp("api") / "api.SC2Replay"
    out.write_bytes(base64.b64decode((FIXTURES / "api_bot_vs_easy_ai.SC2Replay.b64").read_text()))
    return str(out)


def test_plain_engine_cannot_read_api_replay(api_replay):
    """Documents why replay_compat exists."""
    from sc2um.replay import ReplayError

    with pytest.raises(ReplayError):
        analyze_replay(api_replay)


def test_patch_is_scoped(api_replay):
    from sc2reader import resources

    original = resources.Replay.load_details
    with replay_compat.api_replay_support():
        assert resources.Replay.load_details is not original
    assert resources.Replay.load_details is original


def test_load_api_replay_players(api_replay):
    view = replay_compat.load_api_replay(api_replay)
    assert view.type == "1v1"
    assert view.map_name == "Acropolis LE"
    assert view.build == 75689
    got = [(p.pid, p.name, p.play_race, p.result, p.team_id, p.is_human) for p in view.players]
    assert got == [
        (1, "Local Player", "Protoss", "Win", 1, True),
        (2, "A.I. 1 (Easy)", "Zerg", "Loss", 2, False),
    ]


def test_replay_summary_on_api_replay(api_replay):
    report, text = replay_summary(api_replay)
    bot = report["players"][0]
    assert report["length"] == "06.13"
    assert bot["workers_at"]["3:00"] == 24
    assert bot["workers_at"]["10:00"] is None
    names = [i["name"] for i in bot["build_order"]]
    for needed in ("Pylon", "Gateway", "Assimilator", "CyberneticsCore", "Zealot", "Stalker"):
        assert needed in names
    assert max(s["army_value"] for s in bot["army_timeline"]) > 0
    assert "== Local Player (Protoss, team 1) - Win ==" in text
    assert "== A.I. 1 (Easy) (Zerg, team 2) - Loss ==" in text


def test_compat_loader_still_reads_normal_replays():
    out = base64.b64decode((FIXTURES / "lotv_1v1_pvp.SC2Replay.b64").read_text())
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "n.SC2Replay"
        path.write_bytes(out)
        view = replay_compat.load_api_replay(str(path))
        assert [p.name for p in view.players] == ["Alouette", "PXP"]
        assert view.type == "1v1"


def test_fill_missing_cache_handles():
    raw = {"replay.details": {"cache_handles": []}}
    assert replay_compat.fill_missing_cache_handles(raw) is True
    handle = raw["replay.details"]["cache_handles"][0]
    assert handle.server == "" and handle.hash == replay_compat.VOID_DEPENDENCY_HASH
    assert replay_compat.fill_missing_cache_handles(raw) is False
    assert replay_compat.fill_missing_cache_handles({}) is False
    backup = {"replay.details.backup": {"cache_handles": None}}
    assert replay_compat.fill_missing_cache_handles(backup) is True


def test_players_from_details_skips_observers():
    raw = {"replay.details": {"players": [
        {"name": "Bot", "race": "Protoss", "result": 1, "team": 0, "control": 2, "observe": 0},
        {"name": "Obs", "race": "Terran", "result": 0, "team": 2, "control": 2, "observe": 1},
        {"name": "A.I. 1 (Hard)", "race": "Terran", "result": 3, "team": 1, "control": 3, "observe": 0},
    ]}}
    players = replay_compat.players_from_details(raw)
    assert [(p.pid, p.name, p.result, p.team_id, p.is_human) for p in players] == [
        (1, "Bot", "Win", 1, True),
        (2, "A.I. 1 (Hard)", "Tie", 2, False),
    ]
    assert replay_compat.players_from_details({}) == []
