#!/usr/bin/env python3
"""
Test script for action command detection in Ollama streaming responses.
"""

import asyncio
import re
from backend.services.ollama.ollama_streaming import _detect_and_execute_action_commands, _is_valid_action_command


def test_action_command_validation():
    """Test the action command validation function."""
    print("🧪 Testing action command validation...")
    
    valid_commands = [
        "#help",
        "#render", 
        "#tasks",
        "#analyze",
        "#analyze context",
        "#analyze context reset",
        "#clear all",
        "#clear id 123",
        "#clear group chorus",
        "#add flash to parcan_l at 5.2 duration 1.5",
        "#add strobe to moving_head at 10 duration 2",
        "#flash parcan_pl blue at 5.2s for 1.5s",
        "#fade head_el150 from red to blue at 10s for 3s",
        "#strobe all_parcans at 15s for 2s",
        "#set parcan_l red channel to 0.5 at 12.23s",
        "#preset moving_head Drop at 34.2s"
    ]
    
    invalid_commands = [
        "#this is just text",
        "#not a real command",
        "#random words here",
        "#",
        ""
    ]
    
    print("✅ Valid commands:")
    for cmd in valid_commands:
        result = _is_valid_action_command(cmd)
        print(f"  {cmd} -> {'✓' if result else '✗'}")
        if not result:
            print(f"    ❌ FAILED: Expected valid but got invalid")
    
    print("\n❌ Invalid commands:")
    for cmd in invalid_commands:
        result = _is_valid_action_command(cmd)
        print(f"  {cmd} -> {'✗' if not result else '✓'}")
        if result:
            print(f"    ❌ FAILED: Expected invalid but got valid")


def test_action_command_detection():
    """Test the action command detection in text."""
    print("\n🧪 Testing action command detection in text...")
    
    test_texts = [
        "I'll create a lighting effect for you. #add flash to parcan_l at 5.2 duration 1.5",
        "Let me start by setting up the scene with #render and then #add strobe to moving_head at 10s",
        "You can use these commands:\n- #help\n- #analyze context\n- #clear all",
        "To create this effect, I'll use #flash parcan_pl blue at 5.2s for 1.5s with intensity 0.8",
        "No action commands in this text",
        "Here's a lighting sequence:\n#add flash to parcan_l at 0s\n#add fade to head_el150 at 2s for 3s\n#render"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n📝 Test {i+1}: {text[:50]}...")
        
        # Use the same logic as the actual function
        import re
        
        # Find simple commands first (help, render, tasks, etc.)
        simple_commands = re.findall(r'#(?:action\s+)?(help|render|tasks|analyze(?:\s+context(?:\s+reset)?)?|clear\s+(?:all|id\s+\w+|group\s+\w+))', 
                                   text, re.IGNORECASE)
        
        # Find complex commands with timing (add, flash, fade, etc.)
        complex_pattern = r'#(?:action\s+)?((?:add|flash|fade|strobe|set|preset)\s+[^#\n]*?(?:at|to)\s+[\d.]+[sb]?[^#\n]*?)(?=\s*(?:\n|$|\.|\!|\?|,|\s+#|\s+[A-Z][a-z]))'
        complex_commands = re.findall(complex_pattern, text, re.IGNORECASE | re.DOTALL)
        
        # Combine all found commands
        all_command_texts = [f"#{cmd.strip()}" for cmd in simple_commands + complex_commands]
        
        found_commands = []
        for command_text in all_command_texts:
            if _is_valid_action_command(command_text):
                found_commands.append(command_text)
        
        print(f"  Found {len(found_commands)} action commands:")
        for cmd in found_commands:
            print(f"    🎭 {cmd}")


async def test_mock_command_execution():
    """Test mock execution of detected commands."""
    print("\n🧪 Testing mock command execution...")
    
    class MockActionCommandParser:
        async def parse_command(self, command_text, websocket=None):
            print(f"    🎭 Mock executing: {command_text}")
            return True, f"Mock executed {command_text}", None
    
    class MockWebSocket:
        async def send_json(self, data):
            print(f"    📡 Mock WebSocket send: {data}")
    
    mock_parser = MockActionCommandParser()
    mock_websocket = MockWebSocket()
    executed_commands = set()
    
    test_text = "Let me create a lighting effect. #add flash to parcan_l at 5.2 duration 1.5 and then #render the result."
    
    await _detect_and_execute_action_commands(
        test_text,
        executed_commands,
        mock_parser,
        mock_websocket
    )
    
    print(f"  ✅ Executed commands: {executed_commands}")


async def main():
    """Run all tests."""
    print("🎭 Action Command Detection Test Suite")
    print("=" * 50)
    
    test_action_command_validation()
    test_action_command_detection()
    await test_mock_command_execution()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
