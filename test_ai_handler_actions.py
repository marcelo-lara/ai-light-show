#!/usr/bin/env python3
"""Test script to verify AI handler action processing works correctly."""

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

async def test_action_processing():
    """Test the _process_response_actions function."""
    print("🧪 Testing AI Handler Action Processing")
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
    
    # Test AI response with action commands
    test_response = """Great! I'll create a lighting effect for you.

Let me flash the ParCan lights at different times:

#action flash parcan_l at 1.5s
#action flash parcan_r at 2.0s for 1s
#action strobe moving_head at 3.5s for 2s

This will create a nice synchronized flash sequence across your fixtures!
"""
    
    print("🎭 Testing AI response with embedded actions:")
    print(f"Response: {test_response}")
    print()
    
    # Process the response
    await test_process_response_actions(test_response, mock_websocket)
    
    print(f"\n📊 WebSocket messages sent: {len(mock_websocket.sent_messages)}")
    for i, msg in enumerate(mock_websocket.sent_messages):
        print(f"  {i+1}. {msg['type']}: {msg.get('message', 'N/A')}")
    
    print("\n✨ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_action_processing())
