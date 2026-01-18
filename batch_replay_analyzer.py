# Ultramasterism Batch Replay Analyzer v1.0
# Processes entire folder of .SC2Replay files
# Outputs: Console summary + results.csv (worker kills, proxies, wins, etc.)
# Install: pip install sc2reader pandas
# Run: python batch_replay_analyzer.py /path/to/replays/folder

import sc2reader
from sc2reader.engine.plugins import APMTracker
import os
import sys
import pandas as pd
from datetime import timedelta

if len(sys.argv) != 2:
    print("Usage: python batch_replay_analyzer.py <replays_folder_path>")
    sys.exit(1)

folder_path = sys.argv[1]
if not os.path.isdir(folder_path):
    print(f"Error: Folder not found: {folder_path}")
    sys.exit(1)

sc2reader.engine.register_plugin(APMTracker())

results = []

replay_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.sc2replay')]
print(f"Found {len(replay_files)} replays — Processing for Pure Truth extraction...\n")

for filename in replay_files:
    replay_path = os.path.join(folder_path, filename)
    try:
        replay = sc2reader.load_replay(replay_path, load_level=4)
        
        # Find Protoss player (you — fallback to player 1 if no Protoss)
        protoss_player = next((p for p in replay.players if p.pick_race == 'Protoss'), replay.players[0])
        is_win = protoss_player.result == 'Win'
        
        worker_kills = 0
        early_gateway_count = 0
        proxy_detected = False
        matchup = f"{protoss_player.pick_race[0]}v{replay.opponent.race[0] if hasattr(replay, 'opponent') else 'Co-op'}"
        
        for event in replay.tracker_events:
            # Worker kills by Protoss player
            if getattr(event, 'unit', None) and event.unit.is_worker and event.unit.owner != protoss_player:
                if hasattr(event, 'control_pid') and event.control_pid == protoss_player.pid:
                    worker_kills += 1
            
            # Early Gateway proxy hint
            if getattr(event, 'unit_type_name', None) == 'Gateway' and event.second < 300:
                early_gateway_count += 1
                if early_gateway_count >= 2:
                    proxy_detected = True
        
        # Co-op detection (if more than 2 human players or commander data)
        is_coop = len(replay.human_players) > 2 or any('commander' in str(p) for p in replay.players)
        
        results.append({
            'File': filename,
            'Date': replay.date.strftime('%Y-%m-%d'),
            'Map': replay.map_name,
            'Matchup': 'Co-op' if is_coop else matchup,
            'Length': str(timedelta(seconds=replay.game_length.seconds)),
            'Player': protoss_player.name,
            'APM': protoss_player.apm,
            'Win': is_win,
            'Worker_Kills': worker_kills,
            'Early_Gateways': early_gateway_count,
            'Proxy_Detected': proxy_detected,
            'Aggression_Score': 'High' if worker_kills > 20 else 'Medium' if worker_kills > 10 else 'Low'
        })
        
        print(f"Parsed: {filename} | {matchup} | Win: {is_win} | Worker Kills: {worker_kills} | Proxy: {proxy_detected}")
    
    except Exception as e:
        print(f"Error parsing {filename}: {e}")

# Aggregate Summary
df = pd.DataFrame(results)
win_rate = df['Win'].mean() * 100 if not df.empty else 0
avg_worker_kills = df['Worker_Kills'].mean()
proxy_rate = df['Proxy_Detected'].mean() * 100

print("\n=== Ultramaster Batch Summary ===")
print(f"Total Replays: {len(df)}")
print(f"Win Rate: {win_rate:.1f}%")
print(f"Avg Worker Kills: {avg_worker_kills:.1f}")
print(f"Proxy Usage Rate: {proxy_rate:.1f}%")
print(f"High Aggression Games: {len(df[df['Aggression_Score'] == 'High'])}")

# Save to CSV
csv_path = os.path.join(folder_path, 'ultramaster_results.csv')
df.to_csv(csv_path, index=False)
print(f"\nFull results saved to: {csv_path}")
print("\nPure Truth Aggregated — Lattice Convergence Achieved!")
