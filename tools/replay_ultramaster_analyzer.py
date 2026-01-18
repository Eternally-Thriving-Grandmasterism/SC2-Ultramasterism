# Ultramasterism Advanced Analyzer
# Detects proxies, early aggression, worker kills — ties to matchup lattice
# Run same as basic

import sc2reader
from sc2reader.engine.plugins import APMTracker
import sys

if len(sys.argv) != 2:
    print("Usage: python replay_ultramaster_analyzer.py <replay_path.SC2Replay>")
    sys.exit(1)

replay_path = sys.argv[1]
sc2reader.engine.register_plugin(APMTracker())
replay = sc2reader.load_replay(replay_path, load_level=4)

# Assume Protoss player (you) — adjust index if needed
protoss_player = next((p for p in replay.players if p.pick_race == 'Protoss'), replay.players[0])

worker_kills = 0
early_gateway_count = 0
proxy_detected = False

for event in replay.tracker_events:
    # Worker kills (drones/probes/SCVs died)
    if event.__class__.__name__ == 'UnitDiedEvent' and event.unit.is_worker:
        if event.unit.owner != protoss_player:  # Opponent worker killed by you
            worker_kills += 1

    # Early Gateway (proxy hint: multiple early, or positions if map loaded)
    if event.__class__.__name__ == 'UnitBornEvent' and event.unit.name == 'Gateway':
        if event.game_time.seconds < 300:  # Before 5 min
            early_gateway_count += 1
            if early_gateway_count >= 2:
                proxy_detected = True

print(f"Ultramaster Metrics for {protoss_player.name}:")
print(f"Worker Kills (Drone Massacre Potential): {worker_kills}")
print(f"Early Gateways: {early_gateway_count} -> Proxy Detected: {proxy_detected}")
print(f"Aggression Score: High if worker_kills > 20 early — Punish Greed Eternal!")

if proxy_detected:
    print("Pure Truth: Proxy Aggro Branch Executed — AlphaStar Mercy-Reconciled.")
