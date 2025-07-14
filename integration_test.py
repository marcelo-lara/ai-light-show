#!/usr/bin/env python3
"""
Test script to verify the end-to-end flow
"""

RENDER_DMX = False  # Disable rendering to DMX for this test

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


## 5. Paint Flash of blue color to the RGB Parcan fixture (at 0.5 seconds interval)
print("⛳️ Paint Flash of blue color to the RGB Parcan fixture (at 0.5 seconds interval)...")
for fixture_id, fixture in fixtures.fixtures.items():
    if fixture.fixture_type == 'parcan':
        print(f"  -> {fixture.name} ({fixture.id}) {len(fixture.actions)} actions")
        try:
            # Call the flash action with blue color
            fixture.render_action('flash', {
                'colors': ['blue'],  # Flash with blue color
                'start_time': start_time,
                'duration': duration, 
                'intensity': intensity
            })
            start_time += 0.25  # Increment start time for next fixture
        except ValueError as e:
            print(f"    - {e}")
        except Exception as e:
            print(f"    - Unexpected error: {e}")


## 6. load ActionsSheet for the sample song "born_slippy"
print("⛳️ Load ActionsSheet for the sample song 'born_slippy'...")
from backend.models.actions_sheet import ActionsSheet, ActionModel
actions_sheet = ActionsSheet('born_slippy')

# Load existing actions (or create empty file if it doesn't exist)
actions_sheet.load_actions()

# add a flash action to parcan_pl at start_time with a duration of 0.5 seconds
flash_action = ActionModel(
    action="flash",
    fixture_id="parcan_pl",
    parameters={
        "intensity": 1,
        "colors": ["blue"]
    },
    start_time=start_time,
    duration=0.5
)
actions_sheet.add_action(flash_action)

# Save the actions to file
actions_sheet.save_actions()
print(f"  ✅ Added flash action to parcan_pl at {start_time}s with 0.5s duration")


## 7. Render actions from ActionsSheet at specific timestamps
print("⛳️ Render actions from ActionsSheet at specific timestamps...")
from backend.services.actions_service import ActionsService

# Create the ActionsService with fixtures and dmx_canvas
actions_service = ActionsService(fixtures, dmx_canvas, debug=True)

# Validate the actions before rendering
validation_result = actions_service.validate_actions(actions_sheet)
print(f"  📋 Validation: {validation_result['valid_actions']}/{validation_result['total_actions']} actions valid")
if validation_result['errors']:
    for error in validation_result['errors']:
        print(f"    ❌ {error}")
if validation_result['warnings']:
    for warning in validation_result['warnings']:
        print(f"    ⚠️  {warning}")

# render actions to the dmx_canvas
success = actions_service.render_actions_to_canvas(actions_sheet, clear_first=True)
if success:
    print(f"  ✅ Successfully rendered actions to DMX canvas")
else:
    print(f"  ❌ Failed to render actions to DMX canvas")

# Test rendering actions at a specific timestamp (when our action should be active)
test_timestamp = start_time + 0.1  # During our flash action
render_result = actions_service.render_action_at_time(actions_sheet, test_timestamp)
print(f"  🎯 At {test_timestamp}s: {render_result['active_actions_count']} active actions, {render_result['rendered_count']} rendered")


## 8. Parse action commands from text using Actions Parser Service
print("⛳️ Parse action commands from text using Actions Parser Service...")
from backend.services.actions_parser_service import ActionsParserService

# Create the Actions Parser Service
parser_service = ActionsParserService(fixtures, debug=True)

# Test various command formats
commands_list = [
    "flash parcan_pl blue at 6.0s for 1.0s with intensity 0.8",
    "strobe all_parcans at 7.5s for 2.0s",
    "fade head_el150 from red to blue at 9.0s for 3.0s",
    "full parcan_pr intensity=0.5 at 11.0s for 1.5s",
    "flash parcan_pl blue at 300.0s for 1.0s with intensity 0.8",
]

print(f"  📝 Testing {len(commands_list)} commands:")
parsed_actions = []

for i, command in enumerate(commands_list):
    print(f"    {i+1}. '{command}'")
    actions = parser_service.parse_command(command)
    
    if actions:
        for action in actions:
            # Validate the action
            is_valid, issues = parser_service.validate_action(action)
            if is_valid:
                parsed_actions.append(action)
                actions_sheet.add_action(action)
                print(f"      ✅ Parsed: {action.action} on {action.fixture_id} at {action.start_time}s")
            else:
                print(f"      ❌ Invalid action: {', '.join(issues)}")
    else:
        print(f"      ⚠️  No actions parsed from command")

print(f"  🎯 Successfully parsed and added {len(parsed_actions)} actions to ActionsSheet")

# Save the updated actions sheet
actions_sheet.save_actions()
print(f"  💾 Updated actions sheet saved with {len(actions_sheet)} total actions")

# Show help for supported commands
print("  📖 Supported command formats:")
help_lines = parser_service.get_supported_commands_help().strip().split('\n')
for line in help_lines[:10]:  # Show first 10 lines of help
    print(f"    {line}")
print("    ... (use parser_service.get_supported_commands_help() for full help)")

success = actions_service.render_actions_to_canvas(actions_sheet, clear_first=True)
if success:
    print(f"  ✅ Successfully rendered actions to DMX canvas")
else:
    print(f"  ❌ Failed to render actions to DMX canvas")



## Send the DMX canvas to the artnet node
if RENDER_DMX:
    print("⛳️ Sending DMX canvas to the artnet node...")
    from backend.services.dmx_dispatcher import send_artnet
    import time

    test_duration = start_time + 1.0
    test_fps = 44       # 44 frames per second for testing
    frame_interval = 1.0 / test_fps

    for i in range(int(test_duration * test_fps)):
        current_time = i * frame_interval
        
        # Get the DMX frame for this timestamp
        dmx_frame = dmx_canvas.get_frame(current_time)
        
        # Send the frame via ArtNet (now accepts bytes directly)
        send_artnet(dmx_frame, debug=True)
        
        # Sleep until next frame (for real-time playback)
        time.sleep(frame_interval)
    print("  ✅ ArtNet transmission test completed")



## save the DMX canvas to a file
print("🏁 Saving DMX canvas to file...")
dmx_canvas_file = "integration_test_output.txt"
with open(dmx_canvas_file, 'w') as f:
    f.write(dmx_canvas.export_as_txt(end_channel=45))
