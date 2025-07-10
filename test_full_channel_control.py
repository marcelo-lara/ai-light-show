#!/usr/bin/env python3
"""Test direct channel control functionality end-to-end."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_full_channel_control():
    """Test the complete channel control workflow."""
    
    from backend.ai.cue_interpreter import CueInterpreter
    from backend.services.cue_service import CueManager
    from backend.models.song_metadata import SongMetadata
    
    # Create test components
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    
    # Create a simple test song
    song = SongMetadata("test_song.mp3", ignore_existing=True)
    song.title = "Test Song"
    song.duration = 180.0
    song.bpm = 128
    
    # Create test fixtures
    test_fixtures = [
        {
            "id": "parcan_pl",
            "name": "Parcan Left", 
            "type": "rgb",
            "channels": {"dim": 1, "red": 2, "green": 3, "blue": 4, "strobe": 5}
        },
        {
            "id": "head_el150",
            "name": "Moving Head",
            "type": "moving_head", 
            "channels": {"pan": 1, "tilt": 2, "dim": 3, "color": 4, "shutter": 5}
        }
    ]
    
    # Create test presets
    test_presets = [
        {"name": "Flash Red", "type": "flash"},
        {"name": "Smooth Fade", "type": "fade"}
    ]
    
    print("🧪 Testing Direct Channel Control")
    print("=" * 50)
    
    # Test cases for channel vs preset selection
    test_cases = [
        {
            "command": "set red to 255 on parcan_pl at 30 seconds",
            "expected_mode": "channel",
            "description": "Direct red channel"
        },
        {
            "command": "flash red on parcan_pl at 30 seconds", 
            "expected_mode": "preset",
            "description": "Flash effect (should use preset)"
        },
        {
            "command": "dim to 50% on all fixtures at 45 seconds",
            "expected_mode": "channel",
            "description": "Percentage dimmer"
        },
        {
            "command": "set brightness to 80% and red to 200 on parcan_pl at 1:00",
            "expected_mode": "channel", 
            "description": "Multiple channel values"
        }
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔬 Test {i}: {test['description']}")
        print(f"Command: '{test['command']}'")
        print(f"Expected: {test['expected_mode']} mode")
        
        try:
            # Clear previous cues
            cue_manager.clear_cues()
            
            # Execute command
            success, message = interpreter.execute_command(
                test['command'], song, test_fixtures, test_presets
            )
            
            if success:
                print(f"✅ Success: {message}")
                
                # Check the created cues
                if cue_manager.cue_list:
                    cue = cue_manager.cue_list[0]
                    actual_mode = "channel" if cue.get('type') == 'channel' else "preset"
                    
                    print(f"   Mode: {actual_mode}")
                    if actual_mode == test['expected_mode']:
                        print(f"   ✅ Correct mode!")
                        success_count += 1
                        
                        # Show cue details
                        if actual_mode == "channel":
                            channels = cue.get('channels', {})
                            print(f"   Channels: {channels}")
                        else:
                            preset = cue.get('preset', 'N/A')
                            print(f"   Preset: {preset}")
                    else:
                        print(f"   ❌ Wrong mode! Expected {test['expected_mode']}, got {actual_mode}")
                else:
                    print(f"   ❌ No cues created")
            else:
                print(f"❌ Failed: {message}")
                
        except Exception as e:
            print(f"💥 Error: {e}")
    
    print(f"\n📊 Results: {success_count}/{len(test_cases)} tests passed")
    
    if success_count == len(test_cases):
        print("🎉 All tests passed! Direct channel control is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed.")
        return False

if __name__ == "__main__":
    test_full_channel_control()
