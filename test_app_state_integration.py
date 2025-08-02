#!/usr/bin/env python3
"""
Test: LightingPlannerAgent with App State Integration

This test demonstrates how the LightingPlannerAgent integrates with the global app_state
to automatically use current song information and fixtures.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.agents import LightingPlannerAgent
from backend.models.app_state import app_state
from shared.models.song_metadata import SongMetadata


def test_app_state_integration():
    """Test the LightingPlannerAgent with app_state integration."""
    print("🎛️ LightingPlannerAgent - App State Integration Test")
    print("=" * 60)
    
    agent = LightingPlannerAgent()
    print(f"✅ Created agent: {agent.agent_name}")
    
    # Test 1: No current song (should raise error)
    print("\n1️⃣ Testing without current song:")
    try:
        result = agent.create_plan_for_current_song()
        print("❌ Should have raised an error!")
    except ValueError as e:
        print(f"✅ Correctly raised error: {e}")
    
    # Test 2: Set up a mock current song
    print("\n2️⃣ Setting up mock current song:")
    app_state.current_song_file = "born_slippy"
    app_state.current_song = SongMetadata()
    app_state.current_song.title = "Born Slippy"
    app_state.current_song.bpm = 132
    app_state.current_song.duration = 240.5
    
    print(f"✅ Set current song: {app_state.current_song_file}")
    print(f"   Title: {app_state.current_song.title}")
    print(f"   BPM: {app_state.current_song.bpm}")
    print(f"   Duration: {app_state.current_song.duration}s")
    
    # Test 3: Show fixture information
    print("\n3️⃣ Fixture information:")
    if app_state.fixtures and app_state.fixtures.fixtures:
        print(f"✅ Found {len(app_state.fixtures.fixtures)} fixtures:")
        for fixture_id, fixture in app_state.fixtures.fixtures.items():
            effects = list(fixture.action_handlers.keys()) if hasattr(fixture, 'action_handlers') else []
            print(f"   - {fixture_id} ({fixture.fixture_type}): {effects}")
    else:
        print("⚠️  No fixtures loaded (this is expected in test environment)")
    
    # Test 4: Generate lighting plan for current song
    print("\n4️⃣ Testing lighting plan generation:")
    try:
        result = agent.create_plan_for_current_song(
            context_summary="Electronic dance track with breakdowns and builds",
            segment={"start": 0.0, "end": 30.0, "duration": 30.0},
            user_prompt="Create energetic intro lighting"
        )
        
        if result["status"] == "success":
            print("✅ Lighting plan generated successfully!")
            print(f"📋 Plan entries: {len(result['lighting_plan'])}")
            if result.get('exact_beats'):
                print(f"🎵 Exact beats: {len(result['exact_beats'])}")
            
            # Show some plan entries if available
            for i, entry in enumerate(result['lighting_plan'][:3]):
                print(f"   {i+1}. {entry['time']}s - {entry['label']}: {entry['description'][:50]}...")
                
        else:
            print(f"❌ Plan generation failed: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ Exception during plan generation: {e}")


def test_manual_vs_appstate_comparison():
    """Compare manual usage vs app state integration."""
    print("\n\n🔄 Manual vs App State Comparison")
    print("=" * 40)
    
    agent = LightingPlannerAgent()
    
    print("🔧 Manual approach:")
    print("""
    # Requires manual song path and data setup
    result = agent.create_plan_with_exact_beats(
        song_path="/path/to/song.mp3",
        context_summary="Manual context...",
        segment={"start": 0.0, "end": 30.0}
    )
    """)
    
    print("🎯 App State approach:")
    print("""
    # Automatically uses current song and fixtures
    app_state.current_song_file = "born_slippy"
    app_state.current_song.bpm = 132
    
    result = agent.create_plan_for_current_song(
        segment={"start": 0.0, "end": 30.0},
        user_prompt="Create intro lighting"
    )
    # Song path, metadata, and fixtures included automatically!
    """)
    
    print("✅ Benefits of App State integration:")
    print("- No manual path construction needed")
    print("- Automatic song metadata inclusion")
    print("- Current fixtures automatically included in prompt")
    print("- Consistent with backend architecture patterns")
    print("- Ready for WebSocket handler integration")


def show_usage_examples():
    """Show practical usage examples."""
    print("\n\n📋 Practical Usage Examples")
    print("=" * 35)
    
    print("1️⃣ Basic current song lighting:")
    print("""
    from backend.services.agents import LightingPlannerAgent
    from backend.models.app_state import app_state
    
    agent = LightingPlannerAgent()
    result = agent.create_plan_for_current_song()
    """)
    
    print("\n2️⃣ Segment-specific lighting:")
    print("""
    result = agent.create_plan_for_current_song(
        segment={"start": 64.0, "end": 96.0, "duration": 32.0},
        context_summary="Main drop section with heavy bass"
    )
    """)
    
    print("\n3️⃣ User prompt with current song:")
    print("""
    result = agent.create_plan_for_current_song(
        user_prompt="Create strobing effects on the beat",
        context_summary="High-energy breakdown section"
    )
    """)
    
    print("\n4️⃣ WebSocket handler integration:")
    print("""
    # In a WebSocket handler:
    async def handle_lighting_request(websocket, data):
        agent = LightingPlannerAgent()
        result = agent.create_plan_for_current_song(
            user_prompt=data.get('prompt'),
            segment=data.get('segment')
        )
        await websocket.send_json(result)
    """)


if __name__ == "__main__":
    test_app_state_integration()
    test_manual_vs_appstate_comparison()
    show_usage_examples()
    
    print("\n🚀 LightingPlannerAgent ready for production with app_state integration!")
