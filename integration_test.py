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

## 3. Paint DMX canvas with fixtures actions logic
print("⛳️ Paint DMX canvas with fixtures actions logic...")

print(f"  - arm all fixtures")
for _, fixture in fixtures.fixtures.items():
    print(f"  -> {fixture.name} ({fixture.id}) {len(fixture.actions)} actions")
    try:
        fixture.render_action('arm')
    except ValueError as e:
        print(f"    - {e}")



## save the DMX canvas to a file
print("⛳️ Saving DMX canvas to file...")
dmx_canvas_file = "integration_test_output.txt"
with open(dmx_canvas_file, 'w') as f:
    f.write(dmx_canvas.export_as_txt(end_channel=45))



# for _, fixture in fixtures.fixtures.items():
#     print(f"  -> {fixture.name} ({fixture.id}) {len(fixture.actions)} actions")
#     for action in fixture.actions:
#         print(f"    - {action}")
    