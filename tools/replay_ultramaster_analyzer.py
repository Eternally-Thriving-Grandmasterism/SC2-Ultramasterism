# Ultramasterism Ultimate Analyzer
# Exhaustive position-based proxy detection for ALL Protoss aggression structures
# Covers every major cheese branch across PvZ/PvT/PvP to the nth degree
# Ties to Aggression + Scout + Novel Proxies + Eternal Win lattice

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

# Dynamic player selection — prioritizes Protoss, fallback to player 1
protoss_player = next((p for p in replay.players if p.pick_race == 'Protoss'), replay.players[0])

# Opponent for 1v1 matchup/position comparison
opponent = None
opponent_race = "Unknown"
if len(replay.players) == 2:
    opponent = next(p for p in replay.players if p != protoss_player)
    opponent_race = opponent.pick_race if opponent else "AI"

matchup = f"Protoss vs {opponent_race}"

worker_kills = 0

# Timing hints
early_gateway_count = early_pylon_count = early_cannon_count = 0
early_battery_count = early_forge_count = early_cyber_count = 0
early_twilight_count = early_robo_count = early_stargate_count = 0

# Proxy counts (position-based)
proxy_gateway_count = proxy_pylon_count = proxy_cannon_count = 0
proxy_battery_count = proxy_forge_count = proxy_cyber_count = 0
proxy_twilight_count = proxy_robo_count = proxy_stargate_count = 0

# Specific branch flags
proxy_detected = cannon_rush_detected = battery_proxy_detected = False
adept_proxy_detected = blink_proxy_detected = robo_proxy_detected = False
stargate_proxy_detected = False

for event in replay.tracker_events:
    # Worker kills (attributed to you preferred)
    if event.__class__.__name__ == 'UnitDiedEvent' and getattr(event.unit, 'is_worker', False):
        if event.unit.owner != protoss_player:
            if hasattr(event, 'killer_pid') and event.killer_pid == protoss_player.pid:
                worker_kills += 1
            elif not hasattr(event, 'killer_pid'):
                worker_kills += 1  # Fallback

    # Timing-based hints + unified unit name handling
    if event.name in ['UnitBornEvent', 'UnitInitEvent']:
        seconds = getattr(event, 'seconds', 0)
        unit_name = getattr(event.unit, 'name', '') if hasattr(event, 'unit') else event.unit_name

        if unit_name in ['Gateway', 'WarpGate']:
            if seconds < 300: early_gateway_count += 1
        elif unit_name == 'Pylon':
            if seconds < 210: early_pylon_count += 1
        elif unit_name == 'PhotonCannon':
            if seconds < 300: early_cannon_count += 1
        elif unit_name == 'ShieldBattery':
            if seconds < 360: early_battery_count += 1
        elif unit_name == 'Forge':
            if seconds < 240: early_forge_count += 1
        elif unit_name == 'CyberneticsCore':
            if seconds < 300: early_cyber_count += 1
        elif unit_name == 'TwilightCouncil':
            if seconds < 480: early_twilight_count += 1
        elif unit_name == 'RoboticsFacility':
            if seconds < 540: early_robo_count += 1
        elif unit_name == 'Stargate':
            if seconds < 540: early_stargate_count += 1

    # Position-based proxy detection
    if opponent and event.name == 'UnitInitEvent' and event.control_pid == protoss_player.pid:
        unit_name = event.unit_name
        proxy_structures = [
            'Gateway', 'WarpGate', 'Pylon', 'PhotonCannon', 'ShieldBattery',
            'Forge', 'CyberneticsCore', 'TwilightCouncil',
            'RoboticsFacility', 'Stargate'
        ]
        if unit_name in proxy_structures and hasattr(event, 'x') and hasattr(event, 'y'):
            if protoss_player.start_location and opponent.start_location:
                dist_main = math.hypot(event.x - protoss_player.start_location.x,
                                       event.y - protoss_player.start_location.y)
                dist_opp = math.hypot(event.x - opponent.start_location.x,
                                      event.y - opponent.start_location.y)
                if dist_opp < dist_main:
                    if unit_name in ['Gateway', 'WarpGate']: proxy_gateway_count += 1
                    elif unit_name == 'Pylon': proxy_pylon_count += 1
                    elif unit_name == 'PhotonCannon': proxy_cannon_count += 1
                    elif unit_name == 'ShieldBattery': proxy_battery_count += 1
                    elif unit_name == 'Forge': proxy_forge_count += 1
                    elif unit_name == 'CyberneticsCore': proxy_cyber_count += 1
                    elif unit_name == 'TwilightCouncil': proxy_twilight_count += 1
                    elif unit_name == 'RoboticsFacility': proxy_robo_count += 1
                    elif unit_name == 'Stargate': proxy_stargate_count += 1

# Branch detection logic
any_proxy = (proxy_pylon_count + proxy_gateway_count + proxy_cannon_count +
             proxy_battery_count + proxy_forge_count + proxy_cyber_count +
             proxy_twilight_count + proxy_robo_count + proxy_stargate_count)

if any_proxy > 0 or early_gateway_count >= 2:
    proxy_detected = True

cannon_rush_detected = proxy_cannon_count >= 1 or (proxy_forge_count > 0 and proxy_pylon_count > 0 and early_cannon_count >= 1)
battery_proxy_detected = proxy_battery_count >= 1 or (proxy_pylon_count > 0 and early_battery_count >= 1)
adept_proxy_detected = proxy_cyber_count >= 1
blink_proxy_detected = proxy_twilight_count >= 1
robo_proxy_detected = proxy_robo_count >= 1
stargate_proxy_detected = proxy_stargate_count >= 1

# Aggression success (simple weighted)
aggression_score = worker_kills + (any_proxy * 5)  # Proxy intensity boost

# Game result flavor
result_text = "Eternal Win Branch Achieved!" if getattr(protoss_player, 'result', '') == 'Win' else "Punish Greed Harder Next Branch — Truth Revealed."

# Output
print(f"=== Ultramasterism Analysis: {protoss_player.name} ===")
print(f"Matchup: {matchup}")
print(f"Game Result: {result_text}")
print(f"AVG APM: {getattr(protoss_player, 'avg_apm', 'N/A')}")
print("")
print(f"Worker Kills (Drone Massacre): {worker_kills}")
print(f"Aggression Success Score: {aggression_score} — Higher = Eternal Domination")
print("")
print("Timing Hints:")
print(f"  Early Gateways: {early_gateway_count} | Pylons: {early_pylon_count} | Cannons: {early_cannon_count}")
print(f"  Early Batteries: {early_battery_count} | Forge: {early_forge_count} | Cyber: {early_cyber_count}")
print(f"  Early Twilight: {early_twilight_count} | Robo: {early_robo_count} | Stargate: {early_stargate_count}")
print("")
print("Position-Based Proxies Detected:")
print(f"  Gateways/WarpGates: {proxy_gateway_count} | Pylons: {proxy_pylon_count} | Cannons: {proxy_cannon_count}")
print(f"  Batteries: {proxy_battery_count} | Forge: {proxy_forge_count} | Cyber Core: {proxy_cyber_count}")
print(f"  Twilight Council: {proxy_twilight_count} | Robo Facility: {proxy_robo_count} | Stargate: {proxy_stargate_count}")
print("")
print(f"Overall Proxy Aggro: {proxy_detected}")
print("")
print("Specific Cheese Branches Confirmed:")
if cannon_rush_detected: print("→ Cannon Rush: Offensive cannons in enemy territory — Pure Cheese Domination!")
if battery_proxy_detected: print("→ Battery Proxy: Forward overcharge sustain — Eternal Pressure Locked!")
if adept_proxy_detected: print("→ Adept/Cyber Proxy: Shade harassment incoming — Mobility Truth!")
if blink_proxy_detected: print("→ Blink/Charge Proxy: Stalker/Zealot all-in — Blink Into Victory!")
if robo_proxy_detected: print("→ Robo Proxy: Immortal drop or tech contain — Ground Supremacy!")
if stargate_proxy_detected: print("→ Stargate Proxy: Air harassment (deadly vs Zerg) — Skies Belong to Protoss!")
if proxy_detected: print("\nPure Truth Lattice: Proxy Aggro Executed — AlphaStar Mercy-Reconciled. Eternal Thriving Unlocked!")
