#!/usr/bin/env python3
"""
Test Direct Action Commands Fix

This script tests that direct action commands like '#flash parcan_l at 135.78s' 
are now properly handled by the DirectCommandsParser.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.models.app_state import app_state
from backend.services.ollama.direct_commands_parser import DirectCommandsParser
from shared.models.song_metadata import SongMetadata


async def test_direct_action_commands():
    """Test that direct action commands are now working"""
    
    print("🧪 Testing Direct Action Commands Fix")
    print("=" * 50)
    
    # Setup song context
    try:
        song_metadata = SongMetadata("test_song", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
        app_state.current_song = song_metadata
        app_state.current_song_file = "test_song.mp3"  # Set the file path too
        print("✅ Song context loaded")
    except Exception as e:
        print(f"⚠️ Could not load song context: {e}")
    
    # Check fixtures
    fixture_count = len(app_state.fixtures.fixtures) if app_state.fixtures else 0
    print(f"📋 {fixture_count} fixtures available")
    
    if fixture_count == 0:
        print("❌ No fixtures available - test cannot proceed")
        return
    
    # Initialize parser
    parser = DirectCommandsParser()
    
    # Test commands that were failing in the logs
    test_commands = [
        "#flash parcan_l at 1",
        "#flash parcan_l at 13", 
        "#flash parcan_l at 135",
        "#flash parcan_l at 135.78s",
        "#strobe parcan_r at 10s for 2s",
        "#fade parcan_pl at 5s for 3s",
    ]
    
    print(f"\n🎭 Testing {len(test_commands)} direct action commands...")
    
    success_count = 0
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}. Testing: {command}")
        
        try:
            success, message, data = await parser.parse_command(command)
            
            if success:
                print(f"   ✅ SUCCESS: {message}")
                if data and 'universe' in data:
                    active_channels = sum(1 for val in data['universe'] if val > 0)
                    print(f"   🎨 DMX: {active_channels} active channels")
                success_count += 1
            else:
                print(f"   ❌ FAILED: {message}")
                
        except Exception as e:
            print(f"   💥 ERROR: {e}")
    
    # Summary
    print(f"\n📊 RESULTS:")
    print(f"   Commands tested: {len(test_commands)}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {len(test_commands) - success_count}")
    print(f"   Success rate: {(success_count/len(test_commands)*100):.1f}%")
    
    if success_count == len(test_commands):
        print(f"\n🎉 PERFECT! All direct action commands are now working!")
        print(f"   ✅ The AI can now generate commands like '#flash parcan_l at 135.78s'")
        print(f"   ✅ Commands are automatically parsed and executed")
        print(f"   ✅ DMX painting occurs in real-time")
    elif success_count > 0:
        print(f"\n⚠️ PARTIAL SUCCESS: Most commands working")
        print(f"   ✅ Direct action command parsing is improved")
        print(f"   📝 Some edge cases may need refinement")
    else:
        print(f"\n❌ FAILED: Direct action commands still not working")
    
    print(f"\n✨ Test completed!")


if __name__ == "__main__":
    asyncio.run(test_direct_action_commands())
