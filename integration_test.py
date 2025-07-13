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
from backend.models.fixtures_model import FixturesModel
fixtures = FixturesModel(
    fixtures_config_file=FIXTURES_FILE,
    debug=True
)

## 3. Paint DMX canvas with fixtures actions logic
print("⛳️ Paint DMX canvas with fixtures actions logic...")
for fixture in fixtures.fixtures.values():
    print(f"  -> {fixture.name} (ID: {fixture.id})")
    for action in fixture.actions:
        print(f"    - Action: {action}")
        try:
            # Simulate rendering the action
            fixture.render_action(action, {})
        except ValueError as e:
            print(f"    - Error: {e}")
        except NotImplementedError:
            print(f"    - Action '{action}' is not implemented for fixture '{fixture.name}'")
        else:
            print(f"    - Action '{action}' rendered successfully.")
        print("\n")
    
