"""Run the sc2um bot against StarCraft II's built-in AI and record results.

``python -m sc2um.bot play --race protoss --vs-race random \
    --difficulty Easy --map AcropolisLE --realtime false``

Each game saves its ``.SC2Replay``, writes a JSON result and prints the
sc2um replay-engine summary of the replay. Needs the StarCraft II client
(set ``SC2PATH`` to the install folder, which contains ``Versions/`` and
``Maps/``).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from sc2um.engine import format_clock

DIFFICULTIES = (
    "VeryEasy",
    "Easy",
    "Medium",
    "MediumHard",
    "Hard",
    "Harder",
    "VeryHard",
    "CheatVision",
    "CheatMoney",
    "CheatInsane",
)
BOT_RACES = ("protoss",)
ENEMY_RACES = ("protoss", "terran", "zerg", "random")
LOTV_LOOPS_PER_SECOND = 22.4
DEFAULT_MAP = "AcropolisLE"
DEFAULT_TIME_LIMIT = 2400  # game-clock seconds before the game counts as a tie


def parse_bool(text: str) -> bool:
    value = str(text).strip().lower()
    if value in ("1", "true", "yes", "y", "on"):
        return True
    if value in ("0", "false", "no", "n", "off"):
        return False
    raise argparse.ArgumentTypeError(f"expected true or false, got {text!r}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m sc2um.bot",
        description="Play the sc2um bot against StarCraft II's built-in AI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    play = sub.add_parser("play", help="Play one or more games")
    play.add_argument("--race", choices=BOT_RACES, default="protoss", help="Bot race (only protoss)")
    play.add_argument("--vs-race", choices=ENEMY_RACES, default="random", help="Built-in AI race")
    play.add_argument("--difficulty", choices=DIFFICULTIES, default="Easy", help="Built-in AI difficulty")
    play.add_argument("--map", default=DEFAULT_MAP, help="Map name inside SC2PATH/Maps (e.g. AcropolisLE)")
    play.add_argument("--realtime", type=parse_bool, default=False, help="true or false (default false)")
    play.add_argument("--games", type=int, default=1, help="Number of games to play (default 1)")
    play.add_argument("--out-dir", default="bot-results", help="Folder for replays and JSON results")
    play.add_argument(
        "--game-time-limit",
        type=int,
        default=DEFAULT_TIME_LIMIT,
        help="Game-clock seconds before a game is declared a tie (default 2400)",
    )
    play.add_argument("--no-summary", action="store_true", help="Do not print the replay summary")
    return parser


def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-") or "game"


def game_result(
    *,
    index: int,
    result: str,
    game_loops: int,
    map_name: str,
    difficulty: str,
    vs_race: str,
    realtime: bool,
    replay: Optional[str],
    started_at: str,
    enemy_race_played: Optional[str] = None,
    error: Optional[str] = None,
) -> dict:
    seconds = round(game_loops / LOTV_LOOPS_PER_SECOND, 1) if game_loops else 0.0
    return {
        "game": index,
        "result": result,
        "game_length_seconds": seconds,
        "game_length": format_clock(seconds),
        "game_loops": game_loops,
        "map": map_name,
        "difficulty": difficulty,
        "bot_race": "Protoss",
        "vs_race": vs_race.capitalize(),
        "enemy_race_played": enemy_race_played,
        "realtime": realtime,
        "replay": replay,
        "started_at": started_at,
        "error": error,
    }


def summarize(games: list) -> dict:
    counts = {}
    for game in games:
        counts[game["result"]] = counts.get(game["result"], 0) + 1
    return {
        "games_played": len(games),
        "results": counts,
        "games": games,
    }


def run_one_game(map_name: str, difficulty: str, vs_race: str, realtime: bool, replay_path: str, time_limit: int):
    """Play one game with python-sc2. Returns ``(result_name, game_loops)``."""
    from sc2 import maps
    from sc2.data import Difficulty, Race
    from sc2.main import run_game
    from sc2.player import Bot, Computer

    from sc2um.bot.protoss import ProtossGatewayBot

    bot = ProtossGatewayBot()
    result = run_game(
        maps.get(map_name),
        [Bot(Race.Protoss, bot), Computer(Race[vs_race.capitalize()], Difficulty[difficulty])],
        realtime=realtime,
        save_replay_as=replay_path,
        game_time_limit=time_limit,
    )
    if isinstance(result, list):
        result = result[0]
    name = getattr(result, "name", str(result))
    return name, int(bot.last_game_loop)


def replay_summary(replay_path: str) -> tuple:
    """Run the sc2um replay engine on a saved replay: ``(report, text)``."""
    from sc2um.bot.replay_compat import load_api_replay
    from sc2um.cli import format_summary
    from sc2um.replay import analyze_replay

    report = analyze_replay(load_api_replay(replay_path), minutes=10)
    report["file"] = replay_path
    return report, format_summary(report)


def play(
    args,
    run_game_fn: Optional[Callable] = None,
    summary_fn: Optional[Callable] = None,
    out=None,
) -> dict:
    run_game_fn = run_game_fn or run_one_game
    summary_fn = summary_fn or replay_summary
    out = out or sys.stdout
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    games = []
    for index in range(1, args.games + 1):
        started = datetime.now(timezone.utc)
        stamp = started.strftime("%Y%m%dT%H%M%SZ")
        base = f"{stamp}_g{index}_{slug(args.map)}_{args.difficulty}_vs_{args.vs_race}"
        replay_path = out_dir / f"{base}.SC2Replay"
        error = None
        try:
            result, loops = run_game_fn(
                args.map, args.difficulty, args.vs_race, args.realtime, os.fspath(replay_path), args.game_time_limit
            )
        except Exception as exc:  # report and continue with the next game
            result, loops, error = "Error", 0, f"{type(exc).__name__}: {exc}"
        replay = os.fspath(replay_path) if replay_path.is_file() else None

        enemy_race = None
        summary_text = None
        if replay is not None:
            try:
                report, summary_text = summary_fn(replay)
                bot_player = None
                for player in report.get("players", []):
                    if player.get("is_human") is False or "A.I." in str(player.get("name")):
                        enemy_race = player.get("race")
                    else:
                        bot_player = player
                if enemy_race is None and bot_player is not None:
                    others = [p for p in report["players"] if p is not bot_player]
                    enemy_race = others[0].get("race") if others else None
            except Exception as exc:
                summary_text = f"(replay summary failed: {type(exc).__name__}: {exc})"

        record = game_result(
            index=index,
            result=result,
            game_loops=loops,
            map_name=args.map,
            difficulty=args.difficulty,
            vs_race=args.vs_race,
            realtime=args.realtime,
            replay=replay,
            started_at=started.isoformat(timespec="seconds"),
            enemy_race_played=enemy_race,
            error=error,
        )
        games.append(record)
        (out_dir / f"{base}.json").write_text(json.dumps(record, indent=2))
        print(
            f"Game {index}/{args.games}: {record['result']} in {record['game_length']} "
            f"on {args.map} vs {args.difficulty} {record['enemy_race_played'] or args.vs_race}",
            file=out,
        )
        if error:
            print(f"  error: {error}", file=out)
        if summary_text and not args.no_summary:
            print(summary_text, file=out)

    summary = summarize(games)
    (out_dir / "results.json").write_text(json.dumps(summary, indent=2))
    print(f"Results: {json.dumps(summary['results'])} -> {out_dir / 'results.json'}", file=out)
    return summary


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "play":
        if args.games < 1:
            parser.error("--games must be at least 1")
        summary = play(args)
        errors = summary["results"].get("Error", 0)
        return 1 if errors == summary["games_played"] else 0
    return 1
