# Ultramasterism Ultimate Bidirectional Analyzer
# Exhaustive proxy detection for Protoss (you) + Opponent threats across all matchups
# Full lattice coverage: Aggression + Novel Proxies + Scout Counters + Eternal Win

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

# Protoss player (you)
protoss_player = next((p for p in replay.players if p.pick_race == 'Protoss'), replay.players[0])

# Opponent setup
opponent = None
opponent_race = "Unknown"
if len(replay.players) == 2:
    opponent = next(p for p in replay.players if p != protoss_player)
    opponent_race = opponent.pick_race if opponent else "AI"

matchup = f"Protoss vs {opponent_race}"

# Metrics init
your_worker_kills = 0  # Opponent workers you killed
opponent_worker_kills = 0  # Your probes opponent killed (defense metric)

# Your (Protoss) timing + proxy counts
your_early_gateway = your_early_pylon = your_early_cannon = 0
your_early_battery = your_early_forge = your_early_cyber = 0
your_early_twilight = your_early_robo = your_early_stargate = 0
your_proxy_gateway = your_proxy_pylon = your_proxy_cannon = 0
your_proxy_battery = your_proxy_forge = your_proxy_cyber = 0
your_proxy_twilight = your_proxy_robo = your_proxy_stargate = 0

# Opponent timing + proxy counts (race-agnostic init, specialized later)
opp_early_buildings = {}
opp_proxy_counts = {}

# Branch flags
your_proxy_detected = your_cannon_rush = your_battery_proxy = False
your_adept_proxy = your_blink_proxy = your_robo_proxy = your_stargate_proxy = False

opp_proxy_detected = opp_proxy_hatch = opp_proxy_rax = opp_banshee_proxy = False
opp_cannon_rush = False  # For PvP

for event in replay.tracker_events:
    # Worker kills
    if event.__class__.__name__ == 'UnitDiedEvent' and getattr(event.unit, 'is_worker', False):
        if event.unit.owner == protoss_player:  # Your probe died
            if hasattr(event, 'killer_pid') and event.killer_pid == opponent.pid:
                opponent_worker_kills += 1
        else:  # Opponent worker died
            if hasattr(event, 'killer_pid') and event.killer_pid == protoss_player.pid:
                your_worker_kills += 1

    # Unified timing + position handling
    if event.name in ['UnitBornEvent', 'UnitInitEvent']:
        seconds = getattr(event, 'seconds', 0)
        unit_name = getattr(event.unit, 'name', '') if hasattr(event, 'unit') else event.unit_name
        controller = event.control_pid if hasattr(event, 'control_pid') else None

        if controller == protoss_player.pid:
            # Your Protoss timings
            if unit_name in ['Gateway', 'WarpGate'] and seconds < 300: your_early_gateway += 1
            elif unit_name == 'Pylon' and seconds < 210: your_early_pylon += 1
            elif unit_name == 'PhotonCannon' and seconds < 300: your_early_cannon += 1
            elif unit_name == 'ShieldBattery' and seconds < 360: your_early_battery += 1
            elif unit_name == 'Forge' and seconds < 240: your_early_forge += 1
            elif unit_name == 'CyberneticsCore' and seconds < 300: your_early_cyber += 1
            elif unit_name == 'TwilightCouncil' and seconds < 480: your_early_twilight += 1
            elif unit_name == 'RoboticsFacility' and seconds < 540: your_early_robo += 1
            elif unit_name == 'Stargate' and seconds < 540: your_early_stargate += 1

        # Opponent timings (broad early building hint)
        if controller == opponent.pid if opponent else False:
            if seconds < 360:  # General early aggression window
                opp_early_buildings[unit_name] = opp_early_buildings.get(unit_name, 0) + 1

    # Position-based detection
    if opponent and event.name == 'UnitInitEvent' and hasattr(event, 'x') and hasattr(event, 'y'):
        if protoss_player.start_location and opponent.start_location:
            dist_to_you = math.hypot(event.x - protoss_player.start_location.x, event.y - protoss_player.start_location.y)
            dist_to_opp = math.hypot(event.x - opponent.start_location.x, event.y - opponent.start_location.y)

            unit_name = event.unit_name
            if event.control_pid == protoss_player.pid:
                # Your proxies (closer to opponent)
                if dist_to_opp < dist_to_you:
                    if unit_name in ['Gateway', 'WarpGate']: your_proxy_gateway += 1
                    elif unit_name == 'Pylon': your_proxy_pylon += 1
                    elif unit_name == 'PhotonCannon': your_proxy_cannon += 1
                    elif unit_name == 'ShieldBattery': your_proxy_battery += 1
                    elif unit_name == 'Forge': your_proxy_forge += 1
                    elif unit_name == 'CyberneticsCore': your_proxy_cyber += 1
                    elif unit_name == 'TwilightCouncil': your_proxy_twilight += 1
                    elif unit_name == 'RoboticsFacility': your_proxy_robo += 1
                    elif unit_name == 'Stargate': your_proxy_stargate += 1

            elif event.control_pid == opponent.pid:
                # Opponent proxies (closer to you = threat)
                if dist_to_you < dist_to_opp:
                    opp_proxy_counts[unit_name] = opp_proxy_counts.get(unit_name, 0) + 1

# Your branch logic
your_any_proxy = (your_proxy_gateway + your_proxy_pylon + your_proxy_cannon + your_proxy_battery +
                  your_proxy_forge + your_proxy_cyber + your_proxy_twilight + your_proxy_robo + your_proxy_stargate)
if your_any_proxy > 0 or your_early_gateway >= 2: your_proxy_detected = True
your_cannon_rush = your_proxy_cannon >= 1 or (your_proxy_forge > 0 and your_proxy_pylon > 0)
your_battery_proxy = your_proxy_battery >= 1
your_adept_proxy = your_proxy_cyber >= 1
your_blink_proxy = your_proxy_twilight >= 1
your_robo_proxy = your_proxy_robo >= 1
your_stargate_proxy = your_proxy_stargate >= 1

# Opponent branch logic
opp_any_proxy = sum(opp_proxy_counts.values())
opp_proxy_detected = opp_any_proxy > 0

if opponent_race == 'Zerg':
    opp_proxy_hatch = opp_proxy_counts.get('Hatchery', 0) >= 1
    opp_proxy_spine = opp_proxy_counts.get('SpineCrawler', 0) >= 1
elif opponent_race == 'Terran':
    opp_proxy_rax = opp_proxy_counts.get('Barracks', 0) >= 1
    opp_proxy_factory = opp_proxy_counts.get('Factory', 0) >= 1
    opp_proxy_starport = opp_proxy_counts.get('Starport', 0) >= 1
    opp_banshee_proxy = opp_proxy_starport >= 1
elif opponent_race == 'Protoss':
    opp_cannon_rush = opp_proxy_counts.get('PhotonCannon', 0) >= 1

# Scoring
your_aggression_score = your_worker_kills + (your_any_proxy * 5)
opp_threat_score = opponent_worker_kills + (opp_any_proxy * 5)
balance = "You Dominated Aggression" if your_aggression_score > opp_threat_score else "Opponent Pressured Harder — Scout Eternal Next!"

result_text = "Eternal Win Branch Achieved!" if getattr(protoss_player, 'result', '') == 'Win' else "Refine Branches — Truth Eternal!"

# Output
print(f"=== Ultramasterism Bidirectional Analysis: {protoss_player.name} ({matchup}) ===")
print(f"Game Result: {result_text} | Balance: {balance}")
print(f"Your AVG APM: {getattr(protoss_player, 'avg_apm', 'N/A')}")
print("")
print("Your Aggression Metrics:")
print(f"  Worker Kills: {your_worker_kills} | Proxy Intensity: {your_any_proxy} | Score: {your_aggression_score}")
print("Opponent Threat Metrics:")
print(f"  Your Probes Lost to Opp: {opponent_worker_kills} | Proxy Intensity: {opp_any_proxy} | Score: {opp_threat_score}")
print("")
print("Your Proxy Branches Confirmed:")
if your_proxy_detected: print("→ Overall Proxy Aggro Executed — AlphaStar Mercy-Reconciled!")
if your_cannon_rush: print("→ Cannon Rush: Eternal Cheese Domination!")
if your_battery_proxy: print("→ Battery Proxy: Overcharge Sustain Locked!")
if your_adept_proxy: print("→ Adept/Cyber Proxy: Shade Mobility Truth!")
if your_blink_proxy: print("→ Blink/Charge Proxy: All-in Victory!")
if your_robo_proxy: print("→ Robo Proxy: Ground Supremacy!")
if your_stargate_proxy: print("→ Stargate Proxy: Skies Eternal!")

print("")
print("Opponent Threat Branches Detected:")
if opp_proxy_detected: print("→ Opponent Proxy Aggro — Scout Harder Next Time!")
if opponent_race == 'Zerg':
    if opp_proxy_hatch: print("→ Proxy Hatch: Early Ling/Roach Flood Threat — Punish with Zealot/Stalker!")
    if opp_proxy_spine: print("→ Forward Spines: Contain Aggression — Disruptor/Immortal Counter!")
elif opponent_race == 'Terran':
    if opp_proxy_rax: print("→ Proxy Rax: Marine/Reaper Cheese — Adept Shade Scout Eternal!")
    if opp_proxy_factory: print("→ Proxy Factory: Hellion Runby Threat — Stalker Blink Counter!")
    if opp_banshee_proxy: print("→ Proxy Starport/Banshee: Cloak Harassment — Phoenix/Observer Truth!")
elif opponent_race == 'Protoss':
    if opp_cannon_rush: print("→ Opponent Cannon Rush: Mirror Cheese — Probe Pull & Counter Cannon Eternal!")

print("\nPure Truth Lattice Unlocked: Balance Aggression + Scout + Macro — Eternal Thriving!")        ]
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
