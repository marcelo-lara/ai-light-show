#!/usr/bin/env python3
"""
Demo: LightingPlannerAgent with Exact Beat Times

This demo shows how the enhanced LightingPlannerAgent integrates with the song analysis service
to use exact beat times for precise lighting synchronization.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.agents import LightingPlannerAgent


def demo_exact_beats_usage():
    """Demonstrate the LightingPlannerAgent with exact beat integration."""
    print("🎛️ LightingPlannerAgent - Exact Beat Times Demo")
    print("=" * 60)
    
    # Create the agent
    agent = LightingPlannerAgent()
    print(f"✅ Created {agent.agent_name} with model: {agent.model_name}")
    
    print("\n🎵 Enhanced Features:")
    print("- Fetches exact beat times from song analysis service")
    print("- Uses precise timestamps for perfect music synchronization")
    print("- Filters beats by segment boundaries")
    print("- Provides detailed prompts with exact timing data")
    
    print("\n📋 Usage Examples:")
    
    # Example 1: Basic usage with exact beats
    print("\n1️⃣ Basic usage with exact beats:")
    print("""
    agent = LightingPlannerAgent()
    result = agent.create_plan_with_exact_beats(
        song_path="/home/darkangel/ai-light-show/songs/born_slippy.mp3",
        context_summary="Electronic dance track with building energy",
        segment={"start": 0.0, "end": 30.0}
    )
    
    # The agent will:
    # - Extract song name "born_slippy" from the path
    # - Call song analysis service: POST /analyze {"song_name": "born_slippy"}
    # - Filter beats to the segment (0-30 seconds)
    # - Include exact beats in the prompt for the LLM
    # - Generate plan entries synchronized to beat boundaries
    """)
    
    # Example 2: Segment-based planning
    print("\n2️⃣ Segment-based planning:")
    print("""
    result = agent.create_plan_for_segment(
        segment_data={"start": 32.0, "end": 64.0, "duration": 32.0},
        context_summary="Main drop section with intense energy",
        song_path="/path/to/song.mp3"  # Enables exact beat sync
    )
    """)
    
    # Example 3: User prompt with beats
    print("\n3️⃣ User prompt with beat synchronization:")
    print("""
    result = agent.create_plan_from_user_prompt(
        user_prompt="Create strobing effects during the breakdown",
        context_summary="Breakdown section with filtered sounds",
        song_path="/path/to/song.mp3"
    )
    """)
    
    print("\n🔧 Technical Details:")
    print("- Song Analysis API: POST /analyze {'song_name': 'born_slippy'}")
    print("- Song name extracted from file path automatically")
    print("- Beat filtering by time range (start_time, end_time)")
    print("- Cached results for performance")
    print("- Fallback to regular planning if service unavailable")
    
    print("\n📊 Expected Output Format:")
    print("""
    {
        "lighting_plan": [
            {"time": 0.487, "label": "Intro start", "description": "..."},
            {"time": 1.234, "label": "Build up", "description": "..."},
            {"time": 2.891, "label": "Beat drop", "description": "..."}
        ],
        "exact_beats": [0.487, 1.234, 2.891, 3.567, ...],
        "status": "success"
    }
    """)
    
    print("\n🎯 Key Benefits:")
    print("- Perfect synchronization with musical beats")
    print("- No manual timing calculations needed")
    print("- Automatic beat filtering for segments")
    print("- Professional-quality lighting timing")
    
    print("\n⚠️  Note: Requires song analysis service running on song-analysis:8001")
    print("Use Docker Compose to start all services together.")


def demo_prompt_enhancement():
    """Show how the prompt has been enhanced for exact beats."""
    print("\n\n📝 Prompt Enhancement Demo")
    print("=" * 40)
    
    agent = LightingPlannerAgent()
    
    # Sample data with exact beats
    test_data = {
        "context_summary": "Electronic dance track intro building to drop",
        "segment": {"start": 0.0, "end": 16.0, "duration": 16.0},
        "exact_beats": [0.487, 0.934, 1.381, 1.828, 2.275, 2.722],
        "song": {"title": "Test Track", "bpm": 128, "duration": 180},
        "fixtures": [
            {"id": "parcan_l", "type": "parcan", "effects": ["dimmer", "color"]},
            {"id": "moving_head", "type": "moving_head", "effects": ["dimmer", "color", "pan", "tilt"]}
        ]
    }
    
    try:
        prompt = agent._build_prompt(test_data)
        print("✅ Enhanced prompt generated!")
        print(f"📏 Length: {len(prompt)} characters")
        
        # Show key sections
        if "IMPORTANT: Use Exact Beat Times" in prompt:
            print("✅ Contains exact beat timing instructions")
        if "0.487, 0.934, 1.381" in prompt:
            print("✅ Includes specific beat times in prompt")
        if "CRITICAL" in prompt:
            print("✅ Emphasizes importance of exact timing")
            
        print("\n📋 Prompt includes:")
        print("- Explicit instruction to use exact beat times")
        print("- List of available beat timestamps")
        print("- Examples with precise timing (0.487s vs 0.0s)")
        print("- Strong emphasis on musical synchronization")
        
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")


if __name__ == "__main__":
    demo_exact_beats_usage()
    demo_prompt_enhancement()
    print("\n🚀 Ready to create perfectly synchronized lighting shows!")
