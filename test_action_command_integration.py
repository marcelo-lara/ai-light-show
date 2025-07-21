#!/usr/bin/env python3
"""
Integration test for automatic action command execution from Ollama responses.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from backend.services.ollama.ollama_streaming import query_ollama_streaming


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
    
    async def send_json(self, data):
        self.sent_messages.append(data)
        print(f"📡 WebSocket send: {data}")


class MockOllamaResponse:
    """Mock Ollama response that includes action commands."""
    
    def __init__(self, responses):
        self.responses = responses
        self.index = 0
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        pass
    
    @property
    def content(self):
        return self
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.responses):
            raise StopAsyncIteration
        
        response = self.responses[self.index]
        self.index += 1
        
        # Simulate Ollama streaming response format
        if response == "DONE":
            return json.dumps({"done": True}).encode('utf-8')
        else:
            return json.dumps({
                "message": {"content": response},
                "done": False
            }).encode('utf-8')
    
    def raise_for_status(self):
        pass


async def test_integration():
    """Test the full integration of action command detection and execution."""
    print("🧪 Integration Test: Automatic Action Command Execution")
    print("=" * 60)
    
    # Mock the DirectCommandsParser
    executed_commands = []
    
    class MockDirectCommandsParser:
        async def parse_command(self, command_text, websocket=None):
            executed_commands.append(command_text)
            print(f"    🎭 Mock executing: {command_text}")
            return True, f"Mock executed {command_text}", {"mock": "data"}
    
    # Mock WebSocket
    mock_websocket = MockWebSocket()
    
    # Create mock responses that include action commands
    mock_responses = [
        "I'll create a lighting effect for you. ",
        "Let me start with a flash: ",
        "#add flash to parcan_l at 5.2s duration 1.5s",
        "\n\nThen I'll add a strobe effect: ",
        "#add strobe to moving_head at 10s duration 2s",
        "\n\nFinally, let me render the result: ",
        "#render",
        "\n\nAll done!",
        "DONE"
    ]
    
    # Create chunks received list
    chunks_received = []
    
    async def mock_callback(chunk):
        chunks_received.append(chunk)
        print(f"📦 Chunk received: '{chunk}'")
    
    # Mock the HTTP session and response
    mock_response = MockOllamaResponse(mock_responses)
    
    # Mock aiohttp.ClientSession
    async def mock_post(*args, **kwargs):
        return mock_response
    
    class MockSession:
        def __init__(self):
            self.post = mock_post
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, *args):
            pass
    
    # Mock the imports within the streaming module
    import sys
    from unittest.mock import patch
    
    # Mock the DirectCommandsParser
    with patch('backend.services.ollama.ollama_streaming.DirectCommandsParser', MockDirectCommandsParser):
        # Mock aiohttp.ClientSession
        with patch('aiohttp.ClientSession', MockSession):
            try:
                print("\n🚀 Starting streaming with action command detection...")
                
                response = await query_ollama_streaming(
                    prompt="Create a lighting effect",
                    session_id="test_session",
                    callback=mock_callback,
                    websocket=mock_websocket,
                    auto_execute_commands=True
                )
                
                print(f"\n📝 Full response: {response}")
                print(f"\n📦 Total chunks received: {len(chunks_received)}")
                print(f"🎭 Commands executed: {len(executed_commands)}")
                
                print("\n✅ Executed commands:")
                for cmd in executed_commands:
                    print(f"  - {cmd}")
                
                print(f"\n📡 WebSocket messages sent: {len(mock_websocket.sent_messages)}")
                for msg in mock_websocket.sent_messages:
                    if msg.get('type') == 'actionCommandExecuted':
                        status = "✅" if msg.get('success') else "❌"
                        print(f"  {status} {msg.get('command')}")
                
                # Verify expected commands were executed
                expected_commands = [
                    "#add flash to parcan_l at 5.2s duration 1.5s",
                    "#add strobe to moving_head at 10s duration 2s", 
                    "#render"
                ]
                
                success = True
                for expected in expected_commands:
                    if expected not in executed_commands:
                        print(f"❌ Missing expected command: {expected}")
                        success = False
                
                if success and len(executed_commands) == len(expected_commands):
                    print("\n🎉 Integration test PASSED!")
                else:
                    print("\n💥 Integration test FAILED!")
                    
            except Exception as e:
                print(f"\n💥 Integration test ERROR: {e}")
                import traceback
                traceback.print_exc()


async def main():
    """Run the integration test."""
    await test_integration()


if __name__ == "__main__":
    asyncio.run(main())
