#!/usr/bin/env python3
"""Simple test to check direct channel control functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_channel_parsing():
    """Test the channel parameter parsing."""
    
    from backend.ai.cue_interpreter import CueInterpreter
    from backend.services.cue_service import CueManager
    
    # Initialize
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    
    # Test commands
    test_commands = [
        "set red to 255",
        "dim to 50%", 
        "flash red",
        "set brightness to 80%"
    ]
    
    for command in test_commands:
        print(f"\n🔍 Testing: '{command}'")
        try:
            params = interpreter.parse_effect_parameters(command)
            print(f"   Parsed parameters: {params}")
            
            # Check if channel commands were detected
            has_channels = any(key.startswith('channel_') for key in params.keys())
            print(f"   Has channel commands: {has_channels}")
            
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    test_channel_parsing()
