#!/usr/bin/env python3
"""Test script for direct channel control functionality in the cue interpreter."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.ai.cue_interpreter import CueInterpreter
from backend.services.cue_service import CueManager
from backend.models.song_metadata import SongMetadata
from backend.fixture_utils import load_fixtures_config

def create_test_song():
    """Create a test song with basic metadata."""
    song = SongMetadata("test_song.mp3", ignore_existing=True)
    song.title = "Test Song"
    song.duration = 180.0
    song.bpm = 128
    # Create beat data in the expected format
    beats = []
    for i in range(int(180 * 128 / 60)):
        beat_time = i * (60.0/128)
        beats.append({"time": beat_time, "confidence": 1.0})
    song.beats = beats
    return song

def test_direct_channel_commands():
    """Test direct channel control commands."""
    
    print("🧪 Testing Direct Channel Control Commands")
    print("=" * 60)
    
    # Initialize components
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    song = create_test_song()
    
    # Load fixtures and presets
    try:
        fixtures, presets, _ = load_fixtures_config()
    except Exception as e:
        print(f"❌ Could not load fixture configuration: {e}")
        return False
    
    # Test cases for direct channel control
    test_cases = [
        {
            "command": "set red to 255 on parcans at 30 seconds",
            "description": "Direct red channel control"
        },
        {
            "command": "set blue to 128 and green to 200 on moving heads at 1:00",
            "description": "Multiple channel control"
        },
        {
            "command": "dim to 50% on all rgb fixtures at the drop",
            "description": "Percentage-based dimmer control"
        },
        {
            "command": "set brightness to 80% and red to 255 on left side at 45 seconds",
            "description": "Mixed percentage and direct values"
        },
        {
            "command": "flash red every beat for 8 beats on moving heads at 1:30",
            "description": "Repeating channel-based flash"
        },
        {
            "command": "strobe white every 2 beats for 16 beats on parcans at 2:00",
            "description": "Repeating strobe with color"
        },
        {
            "command": "pan to 180 and tilt to 90 on moving heads at 30 seconds",
            "description": "Position control for moving heads"
        },
        {
            "command": "set white color on rgb fixtures and dim to 100% at 45 seconds",
            "description": "Color name with channel control"
        },
        {
            "command": "pulse green every beat for 4 beats on left side at the chorus",
            "description": "Repeating color pulses"
        },
        {
            "command": "sweep blue to 255 continuously for 10 seconds on all fixtures at 1:15",
            "description": "Continuous effect with specific duration"
        }
    ]
    
    # Track results
    successful_tests = 0
    failed_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        command = test_case["command"]
        description = test_case["description"]
        
        print(f"\n🔬 Test {i}: {description}")
        print(f"Command: \"{command}\"")
        
        try:
            # Clear previous cues
            cue_manager.clear_cues()
            
            # Execute the command
            success, message = interpreter.execute_command(command, song, fixtures, presets)
            
            if success:
                print(f"✅ Success: {message}")
                
                # Check if cues were created with correct structure
                if cue_manager.cue_list:
                    cue = cue_manager.cue_list[0]  # Look at first cue
                    print(f"   📋 Cue details:")
                    print(f"      Time: {cue.get('time', 'N/A')}")
                    print(f"      Fixture: {cue.get('fixture', 'N/A')}")
                    print(f"      Type: {cue.get('type', 'preset')}")
                    
                    # Show channel values if it's a channel-type cue
                    if cue.get('type') == 'channel' and 'channels' in cue:
                        print(f"      Channels: {cue['channels']}")
                    elif 'preset' in cue:
                        print(f"      Preset: {cue['preset']}")
                    
                    print(f"      Total cues created: {len(cue_manager.cue_list)}")
                    
                    # Check for repeating effects
                    if len(cue_manager.cue_list) > 1:
                        times = [c.get('time', 0) for c in cue_manager.cue_list]
                        print(f"      Cue times: {[f'{t:.1f}s' for t in sorted(set(times))]}")
                    
                successful_tests += 1
                
            else:
                print(f"❌ Failed: {message}")
                failed_tests += 1
                
        except Exception as e:
            print(f"💥 Error: {str(e)}")
            failed_tests += 1
    
    # Summary
    print(f"\n📊 Test Summary")
    print(f"=" * 60)
    print(f"Total tests: {len(test_cases)}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {successful_tests/len(test_cases)*100:.1f}%")
    
    if failed_tests == 0:
        print(f"\n🎉 All direct channel control tests passed!")
    else:
        print(f"\n⚠️  Some tests failed - direct channel control may need fixes")
    
    return failed_tests == 0

def test_channel_vs_preset_selection():
    """Test that the system correctly chooses between channel and preset modes."""
    
    print(f"\n🔀 Testing Channel vs Preset Mode Selection")
    print("=" * 60)
    
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    song = create_test_song()
    
    # Load fixtures and presets
    try:
        fixtures, presets, _ = load_fixtures_config()
    except Exception as e:
        print(f"❌ Could not load fixture configuration: {e}")
        return False
    
    # Test cases to verify correct mode selection
    test_cases = [
        {
            "command": "flash red on parcans at 30 seconds",
            "expected_mode": "preset",
            "description": "Should use preset (no specific channel values)"
        },
        {
            "command": "set red to 255 on parcans at 30 seconds", 
            "expected_mode": "channel",
            "description": "Should use channel (specific red value)"
        },
        {
            "command": "bright blue strobe on moving heads at 45 seconds",
            "expected_mode": "preset", 
            "description": "Should use preset (color description, not channel)"
        },
        {
            "command": "dim to 50% on rgb fixtures at 1:00",
            "expected_mode": "channel",
            "description": "Should use channel (specific dim percentage)"
        }
    ]
    
    successful_mode_tests = 0
    
    for i, test_case in enumerate(test_cases, 1):
        command = test_case["command"]
        expected_mode = test_case["expected_mode"]
        description = test_case["description"]
        
        print(f"\n🎯 Mode Test {i}: {description}")
        print(f"Command: \"{command}\"")
        print(f"Expected: {expected_mode} mode")
        
        try:
            cue_manager.clear_cues()
            success, message = interpreter.execute_command(command, song, fixtures, presets)
            
            if success and cue_manager.cue_list:
                cue = cue_manager.cue_list[0]
                actual_mode = "channel" if cue.get('type') == 'channel' else "preset"
                
                if actual_mode == expected_mode:
                    print(f"✅ Correct mode: {actual_mode}")
                    successful_mode_tests += 1
                else:
                    print(f"❌ Wrong mode: got {actual_mode}, expected {expected_mode}")
                    print(f"   Cue structure: {dict(cue)}")
            else:
                print(f"❌ Command failed: {message}")
        
        except Exception as e:
            print(f"💥 Error: {str(e)}")
    
    print(f"\n📊 Mode Selection Results: {successful_mode_tests}/{len(test_cases)} correct")
    return successful_mode_tests == len(test_cases)

if __name__ == "__main__":
    print("🚀 Starting Direct Channel Control Tests")
    print("=" * 60)
    
    # Run all tests
    channel_test_success = test_direct_channel_commands()
    mode_test_success = test_channel_vs_preset_selection()
    
    # Final summary
    print(f"\n🏁 Final Results")
    print("=" * 60)
    
    if channel_test_success and mode_test_success:
        print("🎉 All tests passed! Direct channel control is working correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Direct channel control needs fixes.")
        sys.exit(1)
