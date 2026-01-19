# Ultramasterism Advanced Analyzer
# Enhanced: Position-based proxy detection + better worker kill attribution
# Ties directly to Proxy Aggro + Eternal Win lattice branches

import sc2reader
from sc2reader.engine.plugins import APMTracker
import sys
import math

if len(sys.argv) != 2:
    print("Usage: python replay_ultramaster_analyzer.py <replay_path.SC2Replay>")
    sys.exit(1)

replay_path = sys.argv[1]
sc2reader.engine.register_plugin(APMTracker())
replay = sc2reader.load_replay(replay_path, load_level=4)

# Assume Protoss player (you) — fallback to player 1
protoss_player = next((p for p in replay.players if p.pick_race == 'Protoss'), replay.players[0])

# Find opponent for position comparison (assumes 1v1; skips if team game)
opponent = None
if len(replay.players) == 2:
    opponent = next(p for p in replay.players if p != protoss_player)

worker_kills = 0
early_gateway_count = 0
proxy_gateway_count = 0
proxy_detected = False

for event in replay.tracker_events:
    # Worker kills — prefer attributed to you, fallback to any opponent worker death
    if event.__class__.__name__ == 'UnitDiedEvent' and getattr(event.unit, 'is_worker', False):
        if event.unit.owner != protoss_player:  # Opponent worker
            if hasattr(event, 'killer_pid') and event.killer_pid == protoss_player.pid:
                worker_kills += 1
            elif not hasattr(event, 'killer_pid'):  # Fallback approximation
                worker_kills += 1

    # Timing-based early gateways (kept as legacy hint)
    if event.__class__.__name__ == 'UnitBornEvent' and getattr(event.unit, 'name', '') == 'Gateway':
        if event.seconds < 300:  # Before ~5 min
            early_gateway_count += 1

    # Position-based proxy detection (core new feature)
    if opponent and event.name == 'UnitInitEvent' and event.unit_name in ['Gateway', 'WarpGate']:
        if event.control_pid == protoss_player.pid:
            if (hasattr(event, 'x') and hasattr(event, 'y') and
                protoss_player.start_location and opponent.start_location):
                
                start_x = protoss_player.start_location.x
                start_y = protoss_player.start_location.y
                opp_x = opponent.start_location.x
                opp_y = opponent.start_location.y
                
                dist_main = math.hypot(event.x - start_x, event.y - start_y)
                dist_opp = math.hypot(event.x - opp_x, event.y - opp_y)
                
                if dist_opp < dist_main:  # Closer to opponent = proxy/rush
                    proxy_gateway_count += 1

# Overall proxy detection
if proxy_gateway_count > 0 or early_gateway_count >= 2:
    proxy_detected = True

print(f"Ultramaster Metrics for {protoss_player.name}:")
print(f"Worker Kills (Drone Massacre Potential): {worker_kills}")
print(f"Early Gateways (Timing Hint): {early_gateway_count}")
print(f"Position-Based Proxy Gateways: {proxy_gateway_count}")
print(f"Proxy Detected Overall: {proxy_detected}")
print(f"Aggression Score: High if worker_kills > 20 — Punish Greed Eternal!")

if proxy_detected:
    print("Pure Truth: Proxy Aggro Branch Executed — AlphaStar Mercy-Reconciled.")

if proxy_gateway_count > 0:
    print("Position Analysis: Gateways hidden closer to opponent base — Novel Proxy Branch Confirmed!")
