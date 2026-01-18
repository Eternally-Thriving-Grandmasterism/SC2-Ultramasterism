# Replay Analysis in Ultramasterism

Extract Pure Truth from .SC2Replay files (found in `~/Documents/StarCraft II/Accounts/.../Replays/`).

## Local Python Tools (sc2reader — Offline/Custom)
- Install: `pip install sc2reader`
- Features: Player info, build orders, unit events, APM, worker kills.
- Co-op Support: Yes — commander names, ally/opponent data, unit production.

Code examples in `/tools/`:
- `replay_parser_basic.py`: Load + print basics.
- `replay_ultramaster_analyzer.py`: Lattice metrics (proxy detect, aggression timing, drone kills).

## External Web Tools (Quick Uploads)
- **1v1/Ladder**: Sc2ReplayStats.com (auto-upload app, weakness coaching), SC2 Sensei (macro graphs).
- **Co-op Specific**: starcraft2coop.com/tools/replayanalyzer (calldowns, hero kills).
- **Build Orders**: SpawningTool.com (pro replay search).

Practice Tip: Record duo Brutal+ runs → Parse for "multi-prong efficiency" or mutation counters.
Research Tip: Batch process replays for win-rate sims vs AlphaStar-style greed.
Fun Mode: Compare chaos builds — who proxied harder?

Expand with your PATSAGi replay uploads next!
