#!/usr/bin/env python3
"""
Test script for the improved agents with streaming support and ChatGPT-like UI capabilities.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the backend to the Python path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.services.agents.lighting_planner import LightingPlannerAgent
from backend.services.agents.effect_translator import EffectTranslatorAgent
from backend.models.app_state import app_state


async def test_streaming_callback(chunk: str):
    """Test callback for streaming responses."""
    print(f"📡 Streaming: {chunk}", end="", flush=True)


async def test_lighting_planner():
    """Test the improved LightingPlannerAgent."""
    print("🎛️ Testing Lighting Planner Agent...")
    
    planner = LightingPlannerAgent(model_name="mistral")
    
    # Test data
    input_data = {
        "context_summary": "Upbeat electronic dance track with strong beats, BPM: 128",
        "user_prompt": "Create a plan for the intro with blue chasers and some moving head sweeps",
        "segment": {
            "start": 0.0,
            "end": 30.0,
            "duration": 30.0
        }
    }
    
    print("Testing async method with streaming...")
    result = await planner.run_async(input_data, callback=test_streaming_callback)
    
    print(f"\n✅ Lighting Plan Result:")
    print(f"Status: {result['status']}")
    print(f"Plan entries: {len(result.get('lighting_plan', []))}")
    
    for i, entry in enumerate(result.get('lighting_plan', [])[:3]):  # Show first 3
        print(f"  {i+1}. {entry['time']}s - {entry['label']}: {entry['description']}")
    
    return result


async def test_effect_translator():
    """Test the new EffectTranslatorAgent."""
    print("\n🎭 Testing Effect Translator Agent...")
    
    translator = EffectTranslatorAgent(model_name="mistral")
    
    # Test data - lighting plan entries
    test_plan = [
        {
            "time": 0.5,
            "label": "Intro start",
            "description": "half intensity blue chaser from left to right at 1b intervals"
        },
        {
            "time": 8.2,
            "label": "Build energy",
            "description": "moving head sweep from center to left, then to right"
        }
    ]
    
    input_data = {
        "lighting_plan": test_plan,
        "beat_times": [0.5, 0.9, 1.4, 1.8, 2.3, 2.7, 3.2, 3.6, 4.1, 4.5]  # Sample beats
    }
    
    print("Testing async method with streaming...")
    result = await translator.run_async(input_data, callback=test_streaming_callback)
    
    print(f"\n✅ Translation Result:")
    print(f"Status: {result['status']}")
    print(f"Actions generated: {len(result.get('actions', []))}")
    
    for i, action in enumerate(result.get('actions', [])[:5]):  # Show first 5
        print(f"  {i+1}. {action}")
    
    return result


async def test_single_effect_translation():
    """Test single effect translation."""
    print("\n🎯 Testing Single Effect Translation...")
    
    translator = EffectTranslatorAgent(model_name="mistral")
    
    actions = await translator.translate_single_effect(
        effect_description="strobe all fixtures at high intensity",
        time=10.5,
        duration=2.0,
        callback=test_streaming_callback
    )
    
    print(f"\n✅ Single Effect Actions:")
    for action in actions:
        print(f"  - {action}")
    
    return actions


async def test_convenience_methods():
    """Test convenience methods for ChatGPT-like UI."""
    print("\n🔄 Testing Convenience Methods...")
    
    planner = LightingPlannerAgent(model_name="mistral")
    
    # Test user prompt method
    print("Testing user prompt method...")
    result = await planner.create_plan_from_user_prompt_async(
        user_prompt="Make the lights pulse with the beat during the chorus",
        context_summary="Electronic dance music, BPM: 130",
        callback=test_streaming_callback
    )
    
    print(f"\n✅ User Prompt Result:")
    print(f"Status: {result['status']}")
    print(f"Plan entries: {len(result.get('lighting_plan', []))}")
    
    return result


async def test_error_handling():
    """Test error handling and robustness."""
    print("\n🛡️ Testing Error Handling...")
    
    planner = LightingPlannerAgent(model_name="nonexistent-model")
    
    try:
        result = await planner.run_async({
            "context_summary": "Test song",
            "user_prompt": "Create some lights"
        })
        
        print(f"Error handling result: {result['status']}")
        if result['status'] == 'error':
            print(f"Error message: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"Exception caught: {str(e)}")


async def main():
    """Main test function."""
    print("🚀 Starting AI Light Show Agent Tests...")
    print("=" * 60)
    
    # Test if we can mock some app_state for testing
    print("Setting up test environment...")
    
    try:
        # Test Lighting Planner
        planner_result = await test_lighting_planner()
        
        # Test Effect Translator
        translator_result = await test_effect_translator()
        
        # Test single effect translation
        single_result = await test_single_effect_translation()
        
        # Test convenience methods
        convenience_result = await test_convenience_methods()
        
        # Test error handling
        await test_error_handling()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"- Lighting Planner: {'✅' if planner_result.get('status') == 'success' else '❌'}")
        print(f"- Effect Translator: {'✅' if translator_result.get('status') == 'success' else '❌'}")
        print(f"- Single Effect: {'✅' if single_result else '❌'}")
        print(f"- Convenience Methods: {'✅' if convenience_result.get('status') == 'success' else '❌'}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
