#!/usr/bin/env python3
"""
Test to verify that actions service correctly exports canvas with full song duration + 2 seconds.
This simulates the complete workflow with actions rendering and canvas export.
"""

from backend.config import SONGS_DIR, FIXTURES_FILE
from shared.models.song_metadata import SongMetadata
from backend.services.dmx.dmx_canvas import DmxCanvas
from backend.models.fixtures import FixturesListModel
from backend.services.actions_service import ActionsService
from backend.models.actions_sheet import ActionsSheet, ActionModel
from backend.models.app_state import app_state
import os

print("🧪 Testing Complete Actions Service Canvas Export...")

# 1. Load song metadata
print("1. Loading born_slippy song metadata...")
song_metadata = SongMetadata(
    song_name="born_slippy",
    songs_folder=str(SONGS_DIR),
)
print(f"   📊 Song duration: {song_metadata.duration:.2f}s")

# 2. Set up app state (simulate loading song)
print("2. Setting up app state...")
app_state.current_song = song_metadata
app_state.current_song_file = f"{song_metadata.song_name}.mp3"

# 3. Initialize canvas with song duration + 2 seconds
canvas_duration = song_metadata.duration + 2.0
print(f"3. Initializing canvas with duration: {canvas_duration:.2f}s")
canvas = app_state.reset_dmx_canvas(fps=44, duration=canvas_duration, debug=True)

# 4. Initialize fixtures
print("4. Initializing fixtures...")
fixtures = FixturesListModel(
    fixtures_config_file=FIXTURES_FILE,
    dmx_canvas=canvas,
    debug=True
)

# 5. Create actions service
print("5. Creating actions service...")
actions_service = ActionsService(fixtures, canvas, debug=True)

# 6. Create test actions across the timeline
print("6. Creating test actions across timeline...")
actions_sheet = ActionsSheet(song_metadata.song_name)

# Add actions at different points in the timeline
test_actions = [
    # Start of song
    ActionModel(
        action="flash",
        fixture_id="parcan_l",
        start_time=0.0,
        duration=0.5,
        parameters={"color": "red", "intensity": 1.0}
    ),
    # Middle of song
    ActionModel(
        action="flash",
        fixture_id="parcan_r",
        start_time=song_metadata.duration / 2,
        duration=1.0,
        parameters={"color": "blue", "intensity": 0.8}
    ),
    # Near end of song
    ActionModel(
        action="flash",
        fixture_id="parcan_pl",
        start_time=song_metadata.duration - 5.0,
        duration=2.0,
        parameters={"color": "green", "intensity": 0.6}
    ),
    # In the final effects period (after song ends)
    ActionModel(
        action="flash",
        fixture_id="parcan_pr",
        start_time=song_metadata.duration + 1.0,
        duration=0.8,
        parameters={"color": "white", "intensity": 1.0}
    ),
]

for action in test_actions:
    actions_sheet.add_action(action)

print(f"   ✅ Created {len(test_actions)} test actions")
for i, action in enumerate(test_actions, 1):
    print(f"      {i}. {action.action} on {action.fixture_id} at {action.start_time:.1f}s")

# 7. Render actions to canvas
print("7. Rendering actions to canvas...")
success = actions_service.render_actions_to_canvas(actions_sheet, clear_first=True)
print(f"   📊 Render result: {'SUCCESS' if success else 'FAILED'}")

# 8. Check if canvas file was created
print("8. Checking canvas export file...")
canvas_file = f"{song_metadata.data_folder}/{song_metadata.song_name}.canvas.txt"
if os.path.exists(canvas_file):
    print(f"   ✅ Canvas file exists: {canvas_file}")
    
    # Analyze the file
    with open(canvas_file, 'r') as f:
        lines = f.readlines()
    
    data_lines = [line.strip() for line in lines if line.strip() and line[0].isdigit()]
    if data_lines:
        first_line = data_lines[0]
        last_line = data_lines[-1]
        
        first_time = float(first_line.split(' | ')[0])
        last_time = float(last_line.split(' | ')[0])
        
        print(f"   📈 Canvas timeline: {first_time:.3f}s to {last_time:.3f}s")
        print(f"   📏 Expected duration: {canvas_duration:.3f}s")
        print(f"   ✅ Duration correct: {'YES' if abs(last_time - canvas_duration) < 1.0 else 'NO'}")
        print(f"   🔍 Total data frames: {len(data_lines)}")
        
        # Check for action data
        active_frames = [line for line in data_lines if '255' in line or '204' in line or '153' in line]
        print(f"   💡 Frames with lighting: {len(active_frames)}")
        
        if active_frames:
            print(f"   🎯 Sample active frames:")
            for frame in active_frames[:3]:
                print(f"      {frame}")
            if len(active_frames) > 3:
                print(f"      ... and {len(active_frames) - 3} more")
    
else:
    print(f"   ❌ Canvas file not found: {canvas_file}")

print("✅ Complete actions service canvas export test complete!")
