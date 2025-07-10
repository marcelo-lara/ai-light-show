#!/usr/bin/env python3
"""Test script for the cue interpreter improvements."""

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
]

# Mock song
mock_song = SongMetadata("test_song")
mock_song.duration = 180.0  # 3 minutes
mock_song.bpm = 128
mock_song.arrangement = []

# Test commands from the log
test_commands = [
    "Add white flash effect using parcan lights at the drop",
    "Use multi-colored strobes and fast chasers during the syncopated energy boost, lasting for 15 beats",
    "Create a red pulse effect on right-side fixtures during the Toms and Hihats pattern, lasting for 8 beats",
    "Add purple flash to black, mirrored left and right during the bridge, lasting for 8 beats",
    "Fade back to the beginning pattern during the exit bridge and outro, lasting for 16 beats"
]

def test_interpreter():
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    
    print("🧪 Testing CueInterpreter improvements...")
    print("=" * 60)
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n📝 Test {i}: {command}")
        print("-" * 40)
        
        try:
            interpretation = interpreter.interpret_command(
                command, mock_song, mock_fixtures, mock_presets
            )
            
            print(f"✅ Interpretation successful:")
            print(f"   Operation: {interpretation['operation']}")
            print(f"   Time: {interpretation['time']}")
            print(f"   Fixtures: {interpretation['fixtures']}")
            print(f"   Preset: {interpretation['preset']}")
            print(f"   Parameters: {interpretation['parameters']}")
            print(f"   Confidence: {interpretation['confidence']:.2f}")
            
            # Test execution
            success, message = interpreter.execute_command(
                command, mock_song, mock_fixtures, mock_presets
            )
            
            print(f"🎯 Execution: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"   Message: {message}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_interpreter()
