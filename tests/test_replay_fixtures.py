"""Tests against real replays from sc2reader's test suite (see fixtures/README.md)."""

import json

import pytest

from sc2um import analyze_replay, load_replay
from sc2um.cli import main
from sc2um.replay import ReplayError, frames_per_clock_second


def test_load_replay_1v1(replay_1v1):
    replay = load_replay(replay_1v1)
    assert replay.map_name == "Kairos Junction LE"
    assert frames_per_clock_second(replay) == pytest.approx(22.4)


def test_analyze_1v1_players(replay_1v1):
    report = analyze_replay(replay_1v1)
    assert report["type"] == "1v1"
    assert report["length"] == "07.48"
    players = {p["name"]: p for p in report["players"]}
    assert set(players) == {"Alouette", "PXP"}
    assert players["Alouette"]["race"] == "Protoss"
    assert players["Alouette"]["result"] == "Win"
    assert players["PXP"]["result"] == "Loss"


def test_analyze_1v1_build_order(replay_1v1):
    report = analyze_replay(replay_1v1, minutes=2)
    alouette = next(p for p in report["players"] if p["name"] == "Alouette")
    names = [i["name"] for i in alouette["build_order"]]
    assert names[:5] == ["Probe", "Pylon", "Probe", "Probe", "Gateway"]
    pylon = alouette["build_order"][1]
    assert pylon == {
        "clock": "00:17",
        "seconds": pytest.approx(17.59, abs=0.01),
        "name": "Pylon",
        "kind": "structure",
        "event": "started",
        "supply": "14/15",
    }
    assert all(i["seconds"] <= 120 for i in alouette["build_order"])
    assert "Nexus" in names and "CyberneticsCore" in names


def test_analyze_1v1_workers_and_army(replay_1v1):
    report = analyze_replay(replay_1v1)
    alouette = next(p for p in report["players"] if p["name"] == "Alouette")
    # The game lasts 7:48, so there is no 10:00 count.
    assert alouette["workers_at"] == {"3:00": 26, "6:00": 21, "10:00": None}
    timeline = alouette["army_timeline"]
    assert timeline, "expected stats samples"
    assert max(s["army_value"] for s in timeline) > 0
    assert timeline == sorted(timeline, key=lambda s: s["seconds"])


def test_analyze_team_game(replay_2v2):
    report = analyze_replay(replay_2v2, minutes=3)
    assert report["type"] == "2v2"
    players = report["players"]
    assert len(players) == 4
    assert sorted(p["team"] for p in players) == [1, 1, 2, 2]
    assert {p["result"] for p in players} == {"Win", "Loss"}
    for p in players:
        assert p["build_order"], p["name"]
        assert p["workers_at"]["3:00"] is not None
        assert p["workers_at"]["10:00"] is None  # game is 9:13 long


def test_json_is_serialisable(replay_2v2):
    report = analyze_replay(replay_2v2)
    assert json.loads(json.dumps(report))["players"][0]["name"] == "TcAA"


def test_cli_text(replay_1v1, capsys):
    assert main(["analyze", replay_1v1, "--minutes", "3"]) == 0
    out = capsys.readouterr().out
    assert "Map: Kairos Junction LE" in out
    assert "== Alouette (Protoss, team 1) - Win ==" in out
    assert "Build order (first 3 min):" in out
    assert "00:17    14/15  Pylon" in out
    assert "Workers: 3:00 26, 6:00 21, 10:00 -" in out


def test_cli_json(replay_2v2, capsys):
    assert main(["analyze", replay_2v2, "--json", "--minutes", "1"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["minutes_analyzed"] == 1
    assert len(data["players"]) == 4
    for p in data["players"]:
        assert all(i["seconds"] <= 60 for i in p["build_order"])


def test_clock_rate_follows_build():
    from types import SimpleNamespace

    assert frames_per_clock_second(SimpleNamespace(build=38749)) == pytest.approx(22.4)
    assert frames_per_clock_second(SimpleNamespace(build=34784)) == pytest.approx(22.4)
    assert frames_per_clock_second(SimpleNamespace(build=26490)) == pytest.approx(16.0)
    assert frames_per_clock_second(SimpleNamespace()) == pytest.approx(16.0)


def test_replay_without_tracker_events():
    from types import SimpleNamespace

    players = [SimpleNamespace(pid=1, name="A", play_race="Terran", result="Win", team_id=1)]
    fake = SimpleNamespace(players=players, tracker_events=[], build=26490, frames=16 * 300, map_name="M")
    report = analyze_replay(fake)
    assert report["notes"] and "no tracker events" in report["notes"][0]
    assert report["players"][0]["result"] == "Win"
    assert report["players"][0]["workers_at"] == {"3:00": None, "6:00": None, "10:00": None}


def test_cli_missing_file(tmp_path, capsys):
    assert main(["analyze", str(tmp_path / "nope.SC2Replay")]) == 2
    assert "Replay not found" in capsys.readouterr().err


def test_cli_bad_file(tmp_path, capsys):
    bad = tmp_path / "bad.SC2Replay"
    bad.write_bytes(b"not a replay")
    assert main(["analyze", str(bad)]) == 2
    assert "Could not read replay" in capsys.readouterr().err


def test_load_missing_raises(tmp_path):
    with pytest.raises(ReplayError):
        load_replay(str(tmp_path / "missing.SC2Replay"))


def test_module_entry_point(replay_1v1):
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "sc2um", "analyze", replay_1v1, "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(result.stdout)["map"] == "Kairos Junction LE"
