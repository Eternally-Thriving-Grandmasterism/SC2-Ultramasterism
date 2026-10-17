"""Command line interface: ``python -m sc2um analyze <replay>``."""

from __future__ import annotations

import argparse
import json
import sys

from sc2um.engine import format_clock, per_minute
from sc2um.replay import ReplayError, analyze_replay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m sc2um",
        description="StarCraft II replay engine built on sc2reader.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Summarise one .SC2Replay file")
    analyze.add_argument("replay", help="Path to a .SC2Replay file")
    analyze.add_argument("--json", action="store_true", help="Print JSON instead of text")
    analyze.add_argument(
        "--minutes",
        type=float,
        default=10,
        help="Length of the build order window in game-clock minutes (default 10)",
    )
    return parser


def format_summary(report: dict) -> str:
    lines = []
    lines.append(f"Map: {report.get('map')}")
    lines.append(
        f"Type: {report.get('type')}  Length: {report.get('length')}  "
        f"Release: {report.get('release')}"
    )
    for note in report.get("notes", []):
        lines.append(f"Note: {note}")
    minutes = report.get("minutes_analyzed")
    for player in report["players"]:
        lines.append("")
        team = player.get("team")
        team_text = f", team {team}" if team is not None else ""
        lines.append(
            f"== {player['name']} ({player['race']}{team_text}) - {player['result']} =="
        )
        workers = ", ".join(
            f"{k} {'-' if v is None else v}" for k, v in player["workers_at"].items()
        )
        lines.append(f"Workers: {workers}")
        lines.append(f"Build order (first {minutes:g} min):")
        if not player["build_order"]:
            lines.append("  (none)")
        for item in player["build_order"]:
            supply = item["supply"] or "?"
            suffix = "" if item["event"] == "started" else f" ({item['event']})"
            lines.append(f"  {item['clock']}  {supply:>7}  {item['name']}{suffix}")
        lines.append("Army timeline (end of each minute: army supply / army value):")
        timeline = per_minute(player["army_timeline"])
        if not timeline:
            lines.append("  (none)")
        for sample in timeline:
            lines.append(
                f"  {format_clock(sample['seconds'])}  supply {sample['army_supply']:g}"
                f"  value {sample['army_value']}  workers {sample['workers']}"
            )
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "analyze":
        if args.minutes <= 0:
            parser.error("--minutes must be positive")
        try:
            report = analyze_replay(args.replay, minutes=args.minutes)
        except ReplayError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(format_summary(report))
        return 0
    parser.print_help()
    return 1
