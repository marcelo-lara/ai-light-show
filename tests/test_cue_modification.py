#!/usr/bin/env python3
"""Test script specifically for cue modification functionality."""

import sys
import os
sys.path.insert(0, '/home/darkangel/ai-light-show')

from backend.ai.cue_interpreter import CueInterpreter
from backend.services.cue_service import CueManager
from backend.models.song_metadata import SongMetadata

# Mock fixtures and presets
mock_fixtures = [
    {'id': 'parcan_pl', 'name': 'Parcan Post Left', 'type': 'rgb'},
    {'id': 'parcan_pr', 'name': 'Parcan Post Right', 'type': 'rgb'},
    {'id': 'parcan_l', 'name': 'Parcan Left', 'type': 'rgb'},
    {'id': 'parcan_r', 'name': 'Parcan Right', 'type': 'rgb'},
]

mock_presets = [
    {'name': 'flash', 'description': 'Flash effect', 'type': 'rgb'},
    {'name': 'fade', 'description': 'Fade effect', 'type': 'rgb'},
    {'name': 'chase', 'description': 'Chase effect', 'type': 'rgb'},
    {'name': 'orange_fade', 'description': 'Orange fade effect', 'type': 'rgb'},
]

# Mock song
mock_song = SongMetadata("test_song")
mock_song.duration = 180.0  # 3 minutes
mock_song.bpm = 128  # Add BPM for beat calculations
mock_song.arrangement = []

def test_cue_modification():
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    
    print("🧪 Testing Cue Modification and Repeating Effects...")
    print("=" * 60)
    
    # Step 1: Test repeating effects
    print("\n📝 Step 1: Testing repeating flash effects...")
    repeating_commands = [
        "Add white flash every beat at 34.2s for 8 beats using parcan lights",
        "Add red strobe at 26.7s lasting for 4 beats using parcan lights",
        "Create blue flash during the drop continuously using all lights",
    ]
    
    for command in repeating_commands:
        print(f"\n   Command: {command}")
        success, message = interpreter.execute_command(
            command, mock_song, mock_fixtures, mock_presets
        )
        print(f"   Result: {'✅' if success else '❌'} {message}")
    
    print(f"\n   Total cues after repeating effects: {len(cue_manager.cue_list)}")
    
    # Group cues by time for better visualization
    time_groups = {}
    for cue in cue_manager.cue_list:
        time_key = f"{cue['time']:.1f}s"
        if time_key not in time_groups:
            time_groups[time_key] = []
        time_groups[time_key].append(f"{cue['fixture']}({cue['preset']})")
    
    for time_key in sorted(time_groups.keys()):
        fixtures = time_groups[time_key]
        print(f"      - {time_key}: {', '.join(fixtures)}")
    
    # Step 2: Test single cues (original behavior)
    print("\n📝 Step 2: Adding single-event cues...")
    add_commands = [
        "Add orange fade at 50.0s using parcan lights",
    ]
    
    for command in add_commands:
        print(f"\n   Command: {command}")
        success, message = interpreter.execute_command(
            command, mock_song, mock_fixtures, mock_presets
        )
        print(f"   Result: {'✅' if success else '❌'} {message}")
    
    # Step 3: Try to modify existing cues
    print("\n📝 Step 3: Testing modification commands...")
    modify_commands = [
        "Change the white flash at 34.2s to orange fade",
        "Modify the effect at 26.7s to use chase every 2 beats for 6 beats",
    ]
    
    for command in modify_commands:
        print(f"\n   Command: {command}")
        
        # Check interpretation
        interpretation = interpreter.interpret_command(
            command, mock_song, mock_fixtures, mock_presets
        )
        print(f"   Operation detected: {interpretation['operation']}")
        print(f"   Time: {interpretation['time']}")
        print(f"   Repeat mode: {interpretation['parameters'].get('repeat_mode', 'single')}")
        
        # Try execution
        success, message = interpreter.execute_command(
            command, mock_song, mock_fixtures, mock_presets
        )
        print(f"   Result: {'✅' if success else '❌'} {message}")
    
    print(f"\n   Final total cues: {len(cue_manager.cue_list)}")
    
    print("\n" + "=" * 60)
    print("🏁 Modification and repeating effects test completed!")

if __name__ == "__main__":
    test_cue_modification()
