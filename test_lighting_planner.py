#!/usr/bin/env python3
"""
Test script for the LightingPlannerAgent

This script tests the basic functionality of the LightingPlannerAgent
to ensure it can generate lighting plans from musical context.
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.agents import LightingPlannerAgent


def test_lighting_planner_basic():
    """Test basic lighting planner functionality."""
    print("🧪 Testing LightingPlannerAgent...")
    
    # Create agent instance
    agent = LightingPlannerAgent()
    print(f"✅ Created agent: {agent.agent_name} with model: {agent.model_name}")
    
    # Test data
    test_data = {
        "context_summary": "Energetic electronic intro with building synths and a strong 4/4 beat at 128 BPM. The track starts minimal and builds intensity over 32 seconds.",
        "segment": {
            "start": 0.0,
            "end": 32.0,
            "duration": 32.0
        },
        "song": {
            "title": "Test Track",
            "bpm": 128,
            "duration": 180,
            "beats": [0.0, 0.46875, 0.9375, 1.40625, 1.875, 2.34375]
        },
        "fixtures": [
            {"id": "parcan_l", "type": "parcan", "effects": ["dimmer", "color"]},
            {"id": "parcan_r", "type": "parcan", "effects": ["dimmer", "color"]},
            {"id": "moving_head", "type": "moving_head", "effects": ["dimmer", "color", "pan", "tilt"]}
        ]
    }
    
    try:
        # Run the agent
        print("🚀 Running lighting planner...")
        result = agent.run(test_data)
        
        if result["status"] == "success":
            print("✅ Agent completed successfully!")
            print(f"📋 Generated {len(result['lighting_plan'])} plan entries:")
            
            for entry in result['lighting_plan']:
                print(f"  ⏰ {entry['time']}s - {entry['label']}: {entry['description']}")
                
            print(f"\n📝 Raw response:\n{result['raw_response']}")
            
        else:
            print(f"❌ Agent failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"💥 Test failed with exception: {e}")
        import traceback
        traceback.print_exc()


def test_user_prompt():
    """Test lighting planner with user prompt."""
    print("\n🧪 Testing LightingPlannerAgent with user prompt...")
    
    agent = LightingPlannerAgent()
    
    # Provide minimal song data for template compatibility
    input_data = {
        "user_prompt": "Create a plan for the intro",
        "context_summary": "Electronic dance track with building energy",
        "song": {
            "title": "Test Track",
            "bpm": 128,
            "duration": 180
        },
        "fixtures": [
            {"id": "parcan_l", "type": "parcan", "effects": ["dimmer", "color"]}
        ]
    }
    
    result = agent.run(input_data)
    
    if result["status"] == "success":
        print("✅ User prompt test successful!")
        print(f"📋 Generated {len(result['lighting_plan'])} plan entries")
    else:
        print(f"❌ User prompt test failed: {result.get('error')}")


def test_exact_beats_integration():
    """Test exact beats integration with song analysis service."""
    print("\n🧪 Testing exact beats integration...")
    
    agent = LightingPlannerAgent()
    
    # Test with a song path (this will fail if service unavailable, but that's expected)
    # The agent will extract "born_slippy" from the path
    test_song_path = "/home/darkangel/ai-light-show/songs/born_slippy.mp3"
    
    result = agent.create_plan_with_exact_beats(
        song_path=test_song_path,
        context_summary="Electronic dance track with 128 BPM",
        segment={"start": 0.0, "end": 30.0, "duration": 30.0}
    )
    
    if result["status"] == "success":
        print("✅ Exact beats integration test successful!")
        print(f"📋 Generated {len(result['lighting_plan'])} plan entries")
        if result.get('exact_beats'):
            print(f"🎵 Used {len(result['exact_beats'])} exact beat times")
    else:
        print(f"❌ Exact beats test failed (expected if song analysis service unavailable): {result.get('error')}")


def test_prompt_generation():
    """Test prompt generation without calling LLM."""
    print("\n🧪 Testing prompt generation...")
    
    agent = LightingPlannerAgent()
    
    test_data = {
        "context_summary": "Energetic electronic intro with building synths",
        "segment": {
            "start": 0.0,
            "end": 32.0,
            "duration": 32.0
        },
        "song": {
            "title": "Test Track",
            "bpm": 128,
            "duration": 180,
            "beats": [0.0, 0.46875, 0.9375]
        },
        "fixtures": [
            {"id": "parcan_l", "type": "parcan", "effects": ["dimmer", "color"]}
        ]
    }
    
    try:
        prompt = agent._build_prompt(test_data)
        print("✅ Prompt generated successfully!")
        print(f"📝 Prompt length: {len(prompt)} characters")
        
        # Check if key elements are in the prompt
        if "Test Track" in prompt and "128" in prompt and "parcan_l" in prompt:
            print("✅ Prompt contains expected data!")
        else:
            print("❌ Prompt missing expected data")
            
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")


def test_prompt_parsing():
    """Test the plan response parsing."""
    print("\n🧪 Testing plan response parsing...")
    
    agent = LightingPlannerAgent()
    
    # Test response
    test_response = '''
#plan add at 0.0 "Intro start" "half intensity blue chaser from left to right at 1b intervals"
#plan add at 15.0 "Intro build" "fade from blue to white from right to left every 1b intervals"
#plan add at 31.42 "Intro head" "center sweep the moving head pointing the piano"

Some other text that should be ignored.
#plan add at 45.5 "Drop hit" "full white strobe on all fixtures"
'''
    
    parsed = agent._parse_plan_response(test_response)
    
    print(f"✅ Parsed {len(parsed)} plan entries:")
    for entry in parsed:
        print(f"  ⏰ {entry['time']}s - {entry['label']}: {entry['description']}")
    
    expected_count = 4
    if len(parsed) == expected_count:
        print("✅ Parsing test successful!")
    else:
        print(f"❌ Expected {expected_count} entries, got {len(parsed)}")


if __name__ == "__main__":
    print("🎛️ LightingPlannerAgent Test Suite")
    print("=" * 50)
    
    # Test parsing first (doesn't require LLM)
    test_prompt_parsing()
    
    # Test prompt generation (doesn't require LLM)
    test_prompt_generation()
    
    # Test basic functionality (requires LLM - may fail if service unavailable)
    test_lighting_planner_basic()
    
    # Test user prompt functionality
    test_user_prompt()
    
    # Test exact beats integration (may fail if service unavailable)
    test_exact_beats_integration()
    
    print("\n✨ Test suite completed!")
