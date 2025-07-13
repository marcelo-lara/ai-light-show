#!/usr/bin/env python3
"""
Test script to verify the flow of:
1. initializing the DMX Canvas with a song duration.
2. initialize the fixtures.
3. paint dmx canvas with fixtures actions logic.
"""
    
## 1 Initialize the DMX Canvas with a song duration
print("⛳️ Initializing DMX Canvas with song duration...")
from backend.config import SONGS_DIR
from backend.models.song_metadata import SongMetadata
song_metadata = SongMetadata(
    song_name=f"born_slippy",
    songs_folder=str(SONGS_DIR),
)

from backend.services.dmx_canvas import DmxCanvas
dmx_canvas = DmxCanvas(
    duration=song_metadata.duration,
    debug=True
)

## 2 Initialize the fixtures
print("⛳️ Initialize the fixtures...")
from backend.config import FIXTURES_FILE
from backend.models.fixtures import FixturesListModel
fixtures = FixturesListModel(
    fixtures_config_file=FIXTURES_FILE,
    dmx_canvas=dmx_canvas,
    debug=True
)

## 3. Arm all fixtures with the action logic
print("⛳️ Arm all fixtures with the action logic...")

print(f"  - arm all fixtures")
for _, fixture in fixtures.fixtures.items():
    print(f"  -> {fixture.name} ({fixture.id}) {len(fixture.actions)} actions")
    try:
        fixture.render_action('arm')
    except ValueError as e:
        print(f"    - {e}")


## 4. Paint Flash action to all fixtures with an interval of 0.5 seconds between each fixture
print("⛳️ Paint Flash action to all fixtures with an interval of 0.5 seconds between each fixture...")

start_time = 0.5
duration = 1.0
intensity = 1 # Peak intensity for flash ( 1 = 100% = 255)
for fixture_id, fixture in fixtures.fixtures.items():
    print(f"  -> {fixture.name} ({fixture.id}) {len(fixture.actions)} actions")
    try:
        # Call the flash action with a start time and duration
        fixture.render_action('flash', {
            'start_time': start_time,
            'duration': duration, 
            'intensity': intensity
        })
        start_time += 0.5  # Increment start time for next fixture
    except ValueError as e:
        print(f"    - {e}")
    except Exception as e:
        print(f"    - Unexpected error: {e}")


## save the DMX canvas to a file
print("⛳️ Saving DMX canvas to file...")
dmx_canvas_file = "integration_test_output.txt"
with open(dmx_canvas_file, 'w') as f:
    f.write(dmx_canvas.export_as_txt(end_channel=45))
