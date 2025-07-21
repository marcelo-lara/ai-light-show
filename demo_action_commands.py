#!/usr/bin/env python3
"""
Simple demonstration of automatic action command execution.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from backend.services.ollama.ollama_streaming import _detect_and_execute_action_commands, _is_valid_action_command


class MockDirectCommandsParser:
    """Mock DirectCommandsParser for testing."""
    
    def __init__(self):
        self.executed_commands = []
    
    async def parse_command(self, command_text, websocket=None):
        self.executed_commands.append(command_text)
        print(f"    🎭 Mock executing: {command_text}")
        
        # Simulate different command results
        if "invalid" in command_text.lower():
            return False, f"Invalid command: {command_text}", None
        else:
            return True, f"Successfully executed {command_text}", {"mock": "data"}


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.sent_messages = []
    
    async def send_json(self, data):
        self.sent_messages.append(data)
        print(f"    📡 WebSocket send: {data['type']} - {data['command']} - {'✅' if data['success'] else '❌'}")


async def demo_action_command_detection():
    """Demonstrate action command detection and execution."""
    print("🎭 Demonstration: Automatic Action Command Execution")
    print("=" * 60)
    
    # Create mock objects
    parser = MockDirectCommandsParser()
    websocket = MockWebSocket()
    executed_commands = set()
    
    # Test various AI responses with embedded action commands
    test_responses = [
        {
            "name": "Simple lighting effect",
            "text": "I'll create a lighting effect for you. #add flash to parcan_l at 5.2s duration 1.5s"
        },
        {
            "name": "Multiple commands",
            "text": "Let me set up the scene: #render and then #add strobe to moving_head at 10s for 2s"
        },
        {
            "name": "Complex sequence", 
            "text": """Here's a lighting sequence:
            
            #add flash to parcan_l at 0s
            #add fade to head_el150 at 2s for 3s  
            #flash all_parcans blue at 5s for 1s
            #render
            
            This should create a nice effect!"""
        },
        {
            "name": "Mixed content",
            "text": "To create this effect, I'll use #flash parcan_pl blue at 5.2s for 1.5s with intensity 0.8. You can also try #help for more commands."
        },
        {
            "name": "No commands",
            "text": "This is just regular text without any action commands."
        }
    ]
    
    for i, test in enumerate(test_responses):
        print(f"\n📝 Test {i+1}: {test['name']}")
        print(f"   Text: {test['text'][:60]}...")
        
        # Reset for each test
        executed_commands.clear()
        parser.executed_commands.clear()
        websocket.sent_messages.clear()
        
        # Run the detection and execution
        await _detect_and_execute_action_commands(
            test['text'],
            executed_commands,
            parser,
            websocket
        )
        
        print(f"   📊 Found {len(executed_commands)} commands:")
        for cmd in executed_commands:
            print(f"      🎭 {cmd}")
        
        print(f"   📡 WebSocket messages: {len(websocket.sent_messages)}")
    
    print("\n✅ Demonstration completed!")


def demo_command_validation():
    """Demonstrate command validation logic."""
    print("\n🔍 Command Validation Examples")
    print("-" * 40)
    
    examples = [
        "#help",
        "#render", 
        "#add flash to parcan_l at 5.2s duration 1.5s",
        "#flash all_parcans blue at 10s for 2s",
        "#fade head_el150 from red to blue at 15s",
        "#clear all",
        "#analyze context",
        "#not a real command",
        "#random text here"
    ]
    
    for cmd in examples:
        is_valid = _is_valid_action_command(cmd)
        status = "✅" if is_valid else "❌"
        print(f"  {status} {cmd}")


async def main():
    """Run the demonstration."""
    demo_command_validation()
    await demo_action_command_detection()


if __name__ == "__main__":
    asyncio.run(main())
