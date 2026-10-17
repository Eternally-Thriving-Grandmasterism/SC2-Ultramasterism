**License Update — April 11 2026**  
This project is now under the **Autonomicity Games Sovereign Mercy License (AG-SML) v1.0**.  
Individuals may continue using it freely for personal, educational, research, and daily-living/professional assistance.  
Commercial, enterprise, revenue-generating, or organizational use requires a separate paid commercial license from Autonomicity Games Inc.

**Contact**  
- Primary / security: AlphaProMega@ACityGames.com  
- General inquiries: INFO@ACITYGAMES.COM  
- Direct to CEO / Sherif: CEO@ACITYGAMES.COM

# SC2 Ultramasterism

StarCraft 2 research notes, drafts and experimental replay-analysis scripts, pending human review. It includes a small scripted Protoss bot (sc2um.bot) that plays full games against StarCraft II's built-in AI; results are reported only from logged runs (see Bot engine below).

Part of the Ra-Thor project: [Rathor.ai](https://rathor.ai), inspectable research software.

Contact: info@Rathor.ai

## What's in this repo

### Root
- `LICENSE` — Autonomicity Games Sovereign Mercy License (AG-SML) v1.0.
- `README.md` — This file.
- `batch_replay_analyzer.py` — Python script for batch replay analysis (experimental); walks a folder of `.SC2Replay` files with sc2reader/pandas and writes a CSV summary.
- `calc.Ares-sc2` — Code snippet for Stalker micro using ares/python-sc2 helpers (incomplete, untested).
- `mode.Basic python-sc2` — Code snippet for Disruptor Purification Nova micro (python-sc2 style) (incomplete, untested).

### Queens/
- `Queens/Spores.Snippet` — Code snippet for Oracle Pulsar Beam harass (python-sc2 style) (incomplete, untested).

### coop/
- `coop/commander_duos.m` — Notes and a Mermaid diagram of Co-op commander duo ideas (Protoss + Terran).
- `coop/mutation_counters.md` — Stub notes toward Co-op mutation counters and team-game lattices.

### docs/
- `docs/MERCY_PROTOSS_REPLAY_ANALYSIS_TEMPLATE.md` — Fill-in template for reviewing a Protoss replay (opener, macro timeline, micro moments).
- `docs/MERCY_PROTOSS_VS_TERRAN_ADVANCED_BUILDS_BLUEPRINT.md` — PvT build-order research notes (draft, pending human review) (SkyToss, Disruptor/Immortal, Blink/Adept lines).
- `docs/MERCY_PROTOSS_VS_ZERG_ADVANCED_BUILDS_BLUEPRINT.md` — PvZ advanced build-order research notes (draft, pending human review).
- `docs/MERCY_PROTOSS_VS_ZERG_BLUEPRINT.md` — PvZ phased blueprint (draft, pending human review) (early/mid/late).
- `docs/MERCY_ZERG_ADVANCED_BUILDS_BLUEPRINT.md` — Zerg advanced build-order research notes (draft, pending human review).
- `docs/MERCY_ZERG_REPLAY_ANALYSIS_TEMPLATE.md` — Fill-in template for reviewing a Zerg replay.
- `docs/MERCY_ZERG_VS_PROTOSS_BLUEPRINT.md` — ZvP phased blueprint (draft, pending human review) (early/mid/late).
- `docs/advanced_micro.md` — Short notes on Warp Prism, Disruptor, and Colossus micro themes.
- `docs/co_op_lattice.md` — Co-op commander roster notes and duo practice ideas.
- `docs/co_op_mutation_counters.md` — Co-op mutation counter notes with a Mermaid diagram.
- `docs/colossus_counters.md` — Notes on answering Colossus (positioning, abduct/burst, multi-prong).
- `docs/disruptor_micro.md` — Notes on Disruptor Purification Nova placement and timing.
- `docs/full_matchup_details.md` — Partial matchup notes (PvZ sketch) plus a Co-op Mermaid stub.
- `docs/lattice.md` — ASCII diagram organizing mirror and cross-matchup study branches.
- `docs/practice_drills.md` — Short offline practice-drill ideas.
- `docs/replay_analysis.md` — Notes on local sc2reader tools and external replay sites.
- `docs/research_resources.md` — Short pointer list (AlphaStar paper, python-sc2, Liquipedia, Team Liquid).

### fun/
- `fun/ascii_units.md` — Tiny ASCII art of a Zealot / Zergling gag.

### maps/
- `maps/void_launch.md` — Placeholder notes for map/strategy expansion (including Void Launch / Co-op).

### tools/
- `tools/advanced_build_calculator.py` — Minimal interactive stub that prints a PvZ timing line when that matchup is entered (experimental).
- `tools/build_calculator.py` — Prints fixed PvZ and PvP build-order timing outlines to the console (experimental).
- `tools/integration_guide.py` — Two-line console reminder for installing python-sc2.
- `tools/lattice_visualizer.py` — Experimental NetworkX/Matplotlib script meant to draw a small directed graph of study branches; currently fails on an invalid colour name (powrush_blue).
- `tools/replay_parser_basic.py` — Python script that loads one `.SC2Replay` with sc2reader and prints map, players, chat, and early army events (experimental).
- `tools/replay_ultramaster_analyzer.py` — Python script for single-replay analysis (experimental); attempts proxy/worker-kill heuristics and prints counter notes. Known bugs: some output prints unfilled {…} placeholders, and it can crash on replays with more than 2 players.
- `tools/win_rate_simulator.py` — Tiny random-simulation stub (experimental); not a real performance measure.

### vs_team/
- `vs_team/archon_mode.md` — Mermaid notes on Archon Mode macro/micro role split.

Strategy notes get added only once written.

## Replay engine (sc2um)

`sc2um/` is a small Python package that reads one `.SC2Replay` file with [sc2reader](https://github.com/ggtracker/sc2reader). For each player it reports race, result, build order for the first N minutes, worker count at 3, 6 and 10 minutes, and an army timeline. No StarCraft II install is needed.

```
pip install -r requirements.txt
python -m sc2um analyze path/to/game.SC2Replay              # text summary
python -m sc2um analyze path/to/game.SC2Replay --json       # JSON
python -m sc2um analyze path/to/game.SC2Replay --minutes 6  # shorter build order
python -m pytest                                            # run the tests
```

- Times are the in-game clock (mm:ss). Structures are listed when started; units, morphs and upgrades when completed, since that is when the replay records them. Warp-ins are listed when the warp starts.
- Supply is taken from the most recent stats sample (about every 7 seconds of game clock), so it is approximate.
- Army supply is supply used minus workers. Army value is minerals plus gas of the army alive at that time.
- Replays without tracker data (before patch 2.0.8, and some stripped replays) give only players, races and results.
- Works on 1v1 and team games. Tests use two replays from sc2reader's test suite (see `tests/fixtures/README.md`).

## Bot engine (sc2um.bot)

`sc2um/bot/` is a minimal Protoss bot built on [burnysc2](https://github.com/BurnySc2/python-sc2) (python-sc2). It plays full games against StarCraft II's built-in AI. The plan is fixed and simple:
- train Probes until one base is saturated (16 on minerals, 3 per Assimilator)
- build Pylons when supply runs low
- build up to 4 Gateways, a Cybernetics Core and 2 Assimilators
- train Zealots, plus Stalkers once the Core is ready
- attack with the whole army at 20 army supply, fall back below 6, and defend when enemies come near the base

The decision logic (`sc2um/bot/plan.py`) is unit-tested without the game.

```
# Needs Blizzard's Linux StarCraft II package and a map pack (see licence below);
# set SC2PATH to the extracted StarCraftII folder.
python -m sc2um.bot play --race protoss --vs-race random --difficulty Easy \
    --map AcropolisLE --realtime false --games 1 --out-dir bot-results
```

Each game saves a `.SC2Replay`, writes a JSON result (result, game length, map, difficulty, enemy race) and `results.json`, then prints the replay-engine summary of the replay. The `Bot match` workflow (`.github/workflows/bot-match.yml`, manual dispatch only) downloads the client and the Ladder 2019 Season 3 maps at run time, plays N games and uploads the replays and JSON as artifacts.

**Recorded results (one run, nothing more is claimed):** [run 39010776681](https://github.com/Eternally-Thriving-Grandmasterism/SC2-Ultramasterism/actions/runs/39010776681), 2026-10-17, 3 games vs the built-in AI on **Easy** (race Random; it rolled Terran, Terran, Zerg), AcropolisLE, Linux client 4.10: 3 wins (game clock 06:06, 05:59, 06:04).

**Licence:** the StarCraft II Linux client and map packs are not in this repository. They come from Blizzard under the [StarCraft II AI and Machine Learning License](http://blzdistsc2-a.akamaihd.net/AI_AND_MACHINE_LEARNING_LICENSE.html) ([downloads](https://github.com/Blizzard/s2client-proto#downloads)), which allows AI testing, machine learning and related research only, with no commercial use of the software. The StarCraft II Linux client and maps are used under Blizzard's AI and Machine Learning License (research, non-commercial). Commercial licences under AG-SML cover only this repository's own code and docs, never Blizzard's software, maps or game data.
