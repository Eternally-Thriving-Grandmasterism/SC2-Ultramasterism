# Ultramasterism Basic Replay Parser
# Run: python replay_parser_basic.py path/to/YourReplay.SC2Replay
# Install: pip install sc2reader

import sc2reader
from sc2reader.engine.plugins import APMTracker, SelectionTracker
import sys

if len(sys.argv) != 2:
    print("Usage: python replay_parser_basic.py <replay_path.SC2Replay>")
    sys.exit(1)

replay_path = sys.argv[1]

# Register plugins for APM and selection tracking
sc2reader.engine.register_plugin(APMTracker())
sc2reader.engine.register_plugin(SelectionTracker())

# Load replay (adjust load_level=4 for full events)
replay = sc2reader.load_replay(replay_path, load_level=4)

print(f"Map: {replay.map_name}")
print(f"Date: {replay.date}")
print(f"Game Length: {replay.game_length}")
print(f"Game Type: {replay.type} (Co-op supported!)")

print("\nPlayers:")
for player in replay.players:
    print(f"- {player.name} ({player.pick_race} on Team {player.team}) -> Result: {player.result}")
    print(f"  APM: {player.apm} | EPM: {player.epm}")

print("\nChat Messages:")
for event in replay.chat_events:
    print(f"[{event.time}] {event.player}: {event.message}")

print("\nBasic Build Order (First 20 Unit Born Events):")
count = 0
for event in replay.game_events:
    if hasattr(event, 'unit') and event.unit is not None and event.unit.is_army:
        print(f"[{event.time}] {event.player.name}: {event.unit.name}")
        count += 1
        if count >= 20:
            break

print("\nPure Truth: Replay Parsed — Thriving Extracted!")
