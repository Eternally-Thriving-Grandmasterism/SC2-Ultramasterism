**License Update — April 11 2026**  
This project is now under the **Autonomicity Games Sovereign Mercy License (AG-SML) v1.0**.  
Individuals may continue using it freely for personal, educational, research, and daily-living/professional assistance.  
Commercial, enterprise, revenue-generating, or organizational use requires a separate paid commercial license from Autonomicity Games Inc.

**Contact**  
- Primary / security: AlphaProMega@ACityGames.com  
- General inquiries: INFO@ACITYGAMES.COM  
- Direct to CEO / Sherif: CEO@ACITYGAMES.COM

# SC2 Ultramasterism

StarCraft 2 research notes, drafts and experimental replay-analysis scripts, pending human review. This repository is not an AI that plays StarCraft, and not an engine for Ra-Thor agents.

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
