#!/usr/bin/env python3
"""Test script to verify actions at specific times (like 20.5s) are rendered to canvas."""

import asyncio
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath('.'))

from backend.models.app_state import app_state
from backend.models.fixtures.fixtures_list_model import FixturesListModel
from backend.models.song_metadata import SongMetadata

# Import the function we want to test
async def test_process_response_actions(response: str, websocket):
    """Test wrapper for _process_response_actions since it's private."""
    from backend.services.websocket_handlers.ai_handler import _process_response_actions
    return await _process_response_actions(response, websocket)

class MockWebSocket:
    """Mock WebSocket for testing."""
    def __init__(self):
        self.sent_messages = []
    
    async def send_json(self, data):
        self.sent_messages.append(data)
        print(f"📤 WebSocket message: {data}")

async def test_specific_time_actions():
    """Test actions at specific times like 20.5 seconds."""
    print("🎯 Testing Actions at Specific Times (20.5s)")
    print("=" * 50)
    
    # Setup app state
    try:
        # Use app_state's initialization logic for fixtures
        if app_state.fixtures is None:
            app_state.fixtures = FixturesListModel(
                fixtures_config_file=Path("/home/darkangel/ai-light-show/fixtures/fixtures.json"),
                dmx_canvas=app_state.dmx_canvas
            )
        print(f"✅ Loaded {len(app_state.fixtures.fixtures)} fixtures")
        
        # Setup song context
        song_metadata = SongMetadata("test_song", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
        app_state.current_song = song_metadata
        app_state.current_song_file = "test_song.mp3"
        print("✅ Song context loaded")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return
    
    # Create mock websocket
    mock_websocket = MockWebSocket()
    
    # Test AI response with specific timing (20.5s)
    test_response = """I'll create lighting effects at your specified time!

Here are some effects at 20.5 seconds:

#flash parcan_l at 20.5s
#flash parcan_r at 20.8s
#flash moving_head at 21.0s for 0.5s

This creates a sequence starting at exactly 20.5 seconds!
"""
    
    print("🎭 Testing AI response with 20.5s actions:")
    print(f"Response: {test_response}")
    print()
    
    # Process the response
    await test_process_response_actions(test_response, mock_websocket)
    
    # Check if actions were processed
    print(f"\n📊 WebSocket messages sent: {len(mock_websocket.sent_messages)}")
    for i, msg in enumerate(mock_websocket.sent_messages):
        print(f"  {i+1}. {msg['type']}: {msg.get('message', 'N/A')}")
    
    # Check the actions that were added
    from backend.models.actions_sheet import ActionsSheet
    song_name = Path(app_state.current_song_file).stem
    actions_sheet = ActionsSheet(song_name)
    actions_sheet.load_actions()
    
    print(f"\n🎬 Total actions in sheet: {len(actions_sheet.actions)}")
    
    # Look for actions around 20.5 seconds
    actions_at_20s = [action for action in actions_sheet.actions if 20.0 <= action.start_time <= 21.5]
    print(f"🎯 Actions between 20.0s and 21.5s: {len(actions_at_20s)}")
    for action in actions_at_20s:
        print(f"  - {action.action} on {action.fixture_id} at {action.start_time}s")
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_specific_time_actions())
