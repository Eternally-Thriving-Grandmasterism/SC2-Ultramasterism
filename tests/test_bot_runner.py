"""Tests for the match runner with the game replaced by a fake (no StarCraft II needed)."""

import argparse
import base64
import json
from pathlib import Path

import pytest

from sc2um.bot import runner

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "lotv_1v1_pvp.SC2Replay.b64"


def args_for(tmp_path, *extra):
    return runner.build_parser().parse_args(["play", "--out-dir", str(tmp_path / "out"), *extra])


def test_parser_defaults(tmp_path):
    a = args_for(tmp_path)
    assert (a.race, a.vs_race, a.difficulty, a.map, a.realtime, a.games) == (
        "protoss", "random", "Easy", "AcropolisLE", False, 1,
    )


def test_parser_realtime_values(tmp_path):
    assert args_for(tmp_path, "--realtime", "false").realtime is False
    assert args_for(tmp_path, "--realtime", "True").realtime is True
    with pytest.raises(SystemExit):
        args_for(tmp_path, "--realtime", "maybe")


def test_parser_rejects_unknown_choices(tmp_path):
    for bad in (["--race", "zerg"], ["--difficulty", "Impossible"], ["--vs-race", "xel'naga"]):
        with pytest.raises(SystemExit):
            args_for(tmp_path, *bad)


def test_parse_bool():
    assert runner.parse_bool("yes") and not runner.parse_bool("0")
    with pytest.raises(argparse.ArgumentTypeError):
        runner.parse_bool("")


def test_game_result_fields():
    rec = runner.game_result(
        index=1, result="Victory", game_loops=22400 * 6, map_name="AcropolisLE", difficulty="Easy",
        vs_race="random", realtime=False, replay="r.SC2Replay", started_at="2026-10-17T06:00:00+00:00",
    )
    assert rec["game_length"] == "100:00"
    assert rec["game_length_seconds"] == 6000.0
    assert rec["vs_race"] == "Random"
    assert rec["bot_race"] == "Protoss"


def test_play_writes_json_and_chains_replay_engine(tmp_path):
    """A fake game 'saves' a real replay; the runner must analyse it with sc2um."""
    calls = []

    def fake_game(map_name, difficulty, vs_race, realtime, replay_path, limit):
        calls.append((map_name, difficulty, vs_race, realtime, limit))
        Path(replay_path).write_bytes(base64.b64decode(FIXTURE.read_text()))
        return "Victory", 10493

    import io

    out = io.StringIO()
    a = args_for(tmp_path, "--games", "2", "--difficulty", "Medium", "--map", "AcropolisLE")
    summary = runner.play(a, run_game_fn=fake_game, out=out)
    assert calls == [("AcropolisLE", "Medium", "random", False, 2400)] * 2
    assert summary["games_played"] == 2
    assert summary["results"] == {"Victory": 2}
    game = summary["games"][0]
    assert game["game_length"] == "07:48"
    assert game["replay"].endswith(".SC2Replay") and Path(game["replay"]).is_file()
    saved = json.loads((tmp_path / "out" / "results.json").read_text())
    assert saved == summary
    assert len(list((tmp_path / "out").glob("*_g*.json"))) == 2
    text = out.getvalue()
    assert "Game 1/2: Victory in 07:48 on AcropolisLE vs Medium" in text
    assert "Map: Kairos Junction LE" in text  # replay-engine summary printed


def test_play_records_errors_and_continues(tmp_path):
    def broken(*_):
        raise RuntimeError("SC2 not found")

    import io

    summary = runner.play(args_for(tmp_path, "--games", "2"), run_game_fn=broken, out=io.StringIO())
    assert summary["results"] == {"Error": 2}
    assert summary["games"][0]["error"] == "RuntimeError: SC2 not found"
    assert summary["games"][0]["replay"] is None


def test_enemy_race_from_replay_report(tmp_path):
    def fake_game(*a):
        Path(a[4]).write_bytes(b"x")
        return "Defeat", 2240

    def fake_summary(path):
        report = {"players": [
            {"name": "sc2um", "race": "Protoss", "is_human": True},
            {"name": "A.I. 1 (Easy)", "race": "Zerg", "is_human": False},
        ]}
        return report, "summary"

    import io

    summary = runner.play(args_for(tmp_path), run_game_fn=fake_game, summary_fn=fake_summary, out=io.StringIO())
    assert summary["games"][0]["enemy_race_played"] == "Zerg"
    assert summary["games"][0]["result"] == "Defeat"


def test_main_returns_error_when_all_games_fail(tmp_path, monkeypatch):
    def broken(*_):
        raise RuntimeError("no game")

    monkeypatch.setattr(runner, "run_one_game", broken)
    assert runner.main(["play", "--out-dir", str(tmp_path / "o")]) == 1


def test_bot_class_imports():
    pytest.importorskip("sc2")
    from sc2um.bot.protoss import ProtossGatewayBot
    from sc2um.bot.plan import PlanConfig

    bot = ProtossGatewayBot(PlanConfig(attack_supply=12))
    assert bot.config.attack_supply == 12
    assert bot.attacking is False
