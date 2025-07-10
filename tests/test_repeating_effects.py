#!/usr/bin/env python3
"""Test script for repeating effects functionality."""

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

# Mock song with BPM
mock_song = SongMetadata("test_song")
mock_song.duration = 180.0  # 3 minutes
mock_song.bpm = 128  # Important for beat calculations
mock_song.arrangement = []

def test_repeating_effects():
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    
    print("🧪 Testing Repeating Effects Functionality...")
    print("=" * 60)
    
    # Test commands that should create repeating effects
    test_commands = [
        "Flash every beat at 34.2s for 8 beats using parcan lights",
        "Strobe during the drop for 16 beats",
        "Multi-colored strobes throughout the energy boost",
        "Fast chasers continuously during the bridge",
        "Flash every 2 beats for 12 beats starting at 45s",
        "Pulse effect for 10 seconds at 60s",
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n📝 Test {i}: {command}")
        print("-" * 50)
        
        try:
            # Check interpretation
            interpretation = interpreter.interpret_command(
                command, mock_song, mock_fixtures, mock_presets
            )
            
            print(f"✅ Interpretation:")
            print(f"   Operation: {interpretation['operation']}")
            print(f"   Time: {interpretation['time']}")
            print(f"   Fixtures: {interpretation['fixtures']}")
            print(f"   Preset: {interpretation['preset']}")
            print(f"   Parameters: {interpretation['parameters']}")
            
            # Check for repeat mode
            repeat_mode = interpretation['parameters'].get('repeat_mode')
            if repeat_mode:
                print(f"   🔄 Repeat Mode: {repeat_mode}")
                if 'duration_beats' in interpretation['parameters']:
                    print(f"   ⏱️  Duration: {interpretation['parameters']['duration_beats']} beats")
                if 'beat_interval' in interpretation['parameters']:
                    print(f"   📊 Interval: every {interpretation['parameters']['beat_interval']} beat(s)")
            
            # Execute the command
            cues_before = len(cue_manager.cue_list)
            success, message = interpreter.execute_command(
                command, mock_song, mock_fixtures, mock_presets
            )
            cues_after = len(cue_manager.cue_list)
            cues_added = cues_after - cues_before
            
            print(f"🎯 Execution: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"   Message: {message}")
            print(f"   Cues added: {cues_added}")
            
            # Show some sample cue times if many were created
            if cues_added > 4:
                new_cues = cue_manager.cue_list[-cues_added:]
                sample_times = sorted(set(cue['time'] for cue in new_cues))[:5]
                print(f"   Sample times: {[f'{t:.1f}s' for t in sample_times]}...")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print(f"\n📊 Final Stats:")
    print(f"   Total cues created: {len(cue_manager.cue_list)}")
    
    # Group cues by time to show the pattern
    time_groups = {}
    for cue in cue_manager.cue_list:
        time_key = round(cue['time'], 1)
        if time_key not in time_groups:
            time_groups[time_key] = []
        time_groups[time_key].append(cue)
    
    print(f"   Time slots with cues: {len(time_groups)}")
    
    # Show first few time slots
    sorted_times = sorted(time_groups.keys())[:8]
    for time_slot in sorted_times:
        cues_at_time = time_groups[time_slot]
        print(f"      {time_slot}s: {len(cues_at_time)} cue(s) - {cues_at_time[0]['preset']}")
    
    print("\n" + "=" * 60)
    print("🏁 Repeating effects test completed!")

if __name__ == "__main__":
    test_repeating_effects()
