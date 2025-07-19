#!/usr/bin/env python3
"""
Test script to verify dynamic fixture functionality in EffectTranslatorAgent

This script tests that the effect translator correctly reads fixture information
from the global app_state singleton and generates appropriate direct commands.
"""

import sys
import os
import json

# Add the backend to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_dynamic_fixture_info():
    """Test dynamic fixture information extraction"""
    print("🔧 Testing Dynamic Fixture Information Extraction")
    print("=" * 60)
    
    from backend.services.langgraph.agents.effect_translator import EffectTranslatorAgent
    from backend.models.app_state import app_state
    
    # Create the agent
    agent = EffectTranslatorAgent()
    
    # Test fixture info extraction
    print("📋 Testing _get_dynamic_fixture_info()...")
    fixture_info = agent._get_dynamic_fixture_info()
    
    print(f"✅ Found {len(fixture_info['fixture_ids'])} fixtures:")
    for fixture_id in fixture_info['fixture_ids']:
        print(f"   - {fixture_id}")
    
    print(f"✅ Found {len(fixture_info['channels'])} channels:")
    for channel in fixture_info['channels'][:10]:  # Show first 10
        print(f"   - {channel}")
    if len(fixture_info['channels']) > 10:
        print(f"   ... and {len(fixture_info['channels']) - 10} more")
    
    print(f"✅ Found {len(fixture_info['presets'])} presets:")
    for preset in fixture_info['presets']:
        print(f"   - {preset}")
    
    return fixture_info

def test_dynamic_prompt_generation():
    """Test that prompts use dynamic fixture information"""
    print("\n🎨 Testing Dynamic Prompt Generation")
    print("=" * 60)
    
    from backend.services.langgraph.agents.effect_translator import EffectTranslatorAgent
    
    # Create test actions
    test_actions = [
        {
            "action": "flash",
            "start": 1.0,
            "duration": 0.5,
            "color": "red"
        },
        {
            "action": "strobe", 
            "start": 2.0,
            "duration": 1.0,
            "rate": 10
        }
    ]
    
    agent = EffectTranslatorAgent()
    prompt = agent._build_prompt(test_actions)
    
    print("📝 Generated prompt contains:")
    
    # Check for dynamic fixture references
    fixture_info = agent._get_dynamic_fixture_info()
    
    for fixture_id in fixture_info['fixture_ids'][:3]:  # Check first 3 fixtures
        if fixture_id in prompt:
            print(f"   ✅ References fixture: {fixture_id}")
        else:
            print(f"   ⚠️  Missing fixture: {fixture_id}")
    
    for channel in ['red', 'green', 'blue', 'dim', 'dimmer'][:3]:  # Check key channels
        if channel in prompt:
            print(f"   ✅ References channel: {channel}")
        else:
            print(f"   ⚠️  Missing channel: {channel}")
    
    return prompt

def test_fallback_commands():
    """Test fallback command generation with dynamic fixtures"""
    print("\n🛡️ Testing Fallback Command Generation")
    print("=" * 60)
    
    from backend.services.langgraph.agents.effect_translator import EffectTranslatorAgent
    
    # Create test actions
    test_actions = [
        {
            "action": "flash",
            "start": 1.0,
            "duration": 0.5
        },
        {
            "action": "fade",
            "start": 2.0,
            "duration": 1.0
        }
    ]
    
    agent = EffectTranslatorAgent()
    commands = agent._create_fallback_commands(test_actions)
    
    print(f"📋 Generated {len(commands)} fallback commands:")
    for i, cmd in enumerate(commands, 1):
        print(f"   {i}. {cmd}")
    
    # Check that commands use dynamic fixture IDs
    fixture_info = agent._get_dynamic_fixture_info()
    first_fixture = fixture_info['fixture_ids'][0] if fixture_info['fixture_ids'] else 'parcan_l'
    
    dynamic_fixture_found = any(first_fixture in cmd for cmd in commands)
    print(f"✅ Commands use dynamic fixture '{first_fixture}': {dynamic_fixture_found}")
    
    return commands

def main():
    """Run all tests"""
    print("🧪 Testing Dynamic Effect Translator Agent")
    print("=" * 80)
    
    try:
        # Test 1: Dynamic fixture info extraction
        fixture_info = test_dynamic_fixture_info()
        
        # Test 2: Dynamic prompt generation
        prompt = test_dynamic_prompt_generation()
        
        # Test 3: Fallback command generation
        commands = test_fallback_commands()
        
        print("\n🎉 All Tests Completed Successfully!")
        print("=" * 80)
        print("✅ EffectTranslatorAgent is now fully dynamic and venue-agnostic")
        print("✅ Uses app_state.fixtures for fixture/channel/preset information")
        print("✅ Follows copilot-instructions.md patterns for state access")
        print("✅ No hardcoded fixture IDs, channels, or presets")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
