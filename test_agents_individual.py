#!/usr/bin/env python3
"""
Agent Usage Examples - Individual Agent Testing
Demonstrates how to use each agent independently
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.agents import ContextBuilderAgent, LightingPlannerAgent, EffectTranslatorAgent
from backend.services.langgraph.lighting_pipeline import PipelineState


def test_individual_agents():
    """Test each agent individually to show their capabilities"""
    
    print("🧪 Testing Individual Agents...")
    print("=" * 60)
    
    # Sample segment data
    initial_state: PipelineState = {
        "segment": {
            "name": "Build Up",
            "start": 45.0,
            "end": 60.0,
            "features": {
                "energy": 0.85,
                "valence": 0.9,
                "tempo": 128,
                "key": "Em",
                "loudness": -6.0,
                "danceability": 0.95,
                "instruments": ["kick", "bass", "synth", "lead"]
            }
        },
        "context_summary": "",
        "actions": [],
        "dmx": []
    }
    
    # Test Agent 1: Context Builder
    print("\n🎵 Testing Context Builder Agent...")
    print("-" * 40)
    context_agent = ContextBuilderAgent(model="mixtral")
    state_after_context = context_agent.run(initial_state)
    
    print(f"✓ Context Generated: {state_after_context['context_summary']}")
    
    # Test Agent 2: Lighting Planner  
    print("\n💡 Testing Lighting Planner Agent...")
    print("-" * 40)
    planner_agent = LightingPlannerAgent(model="mixtral")
    state_after_planning = planner_agent.run(state_after_context)
    
    print(f"✓ Actions Generated: {len(state_after_planning['actions'])} lighting actions")
    if state_after_planning['actions']:
        for i, action in enumerate(state_after_planning['actions'][:3]):
            print(f"   {i+1}. {action}")
    
    # Test Agent 3: Effect Translator
    print("\n🎛️ Testing Effect Translator Agent...")
    print("-" * 40)
    translator_agent = EffectTranslatorAgent(model="command-r", fallback_model="mixtral")
    state_after_translation = translator_agent.run(state_after_planning)
    
    print(f"✓ DMX Commands Generated: {len(state_after_translation['dmx'])} commands")
    if state_after_translation['dmx']:
        for i, dmx in enumerate(state_after_translation['dmx'][:3]):
            print(f"   {i+1}. {dmx}")
    
    print("\n" + "=" * 60)
    print("🎉 Individual Agent Testing Complete!")
    
    # Show configuration options
    print("\n⚙️ Agent Configuration Examples:")
    print("-" * 40)
    print("# Custom model configuration:")
    print("context_agent = ContextBuilderAgent(model='llama2')")
    print("planner_agent = LightingPlannerAgent(model='mixtral')")
    print("translator_agent = EffectTranslatorAgent(model='command-r', fallback_model='mixtral')")
    
    print("\n# Agent reuse:")
    print("agent = ContextBuilderAgent()")
    print("result1 = agent.run(state1)")
    print("result2 = agent.run(state2)  # Same agent, different data")
    
    return state_after_translation


def test_partial_pipeline():
    """Test partial pipeline execution - useful for debugging"""
    
    print("\n🔧 Testing Partial Pipeline Execution...")
    print("=" * 60)
    
    # Start with pre-filled context (simulating agent 1 already completed)
    partial_state: PipelineState = {
        "segment": {
            "name": "Drop",
            "start": 60.0,
            "end": 64.0,
            "features": {"energy": 0.98, "tempo": 128}
        },
        "context_summary": "Explosive high-energy drop with pounding kick and screaming synths",
        "actions": [],
        "dmx": []
    }
    
    print("📍 Starting from Agent 2 (Lighting Planner)...")
    
    # Run only lighting planner and effect translator
    planner = LightingPlannerAgent()
    planning_result = planner.run(partial_state)
    
    translator = EffectTranslatorAgent()
    final_result = translator.run(planning_result)
    
    print(f"✓ Partial pipeline completed!")
    print(f"  - Actions: {len(final_result['actions'])}")
    print(f"  - DMX Commands: {len(final_result['dmx'])}")
    
    return final_result


def demonstrate_error_handling():
    """Show how agents handle various error conditions"""
    
    print("\n🛡️ Testing Error Handling...")
    print("=" * 60)
    
    # Test with minimal/missing data
    minimal_state: PipelineState = {
        "segment": {},
        "context_summary": "",
        "actions": [],
        "dmx": []
    }
    
    print("📍 Testing with minimal segment data...")
    context_agent = ContextBuilderAgent()
    result = context_agent.run(minimal_state)
    print(f"✓ Handled gracefully: {result['context_summary'][:100]}...")
    
    # Test effect translator with no actions
    print("\n📍 Testing effect translator with no actions...")
    translator = EffectTranslatorAgent()
    empty_actions_state: PipelineState = {
        "segment": {"name": "test"},
        "context_summary": "test context",
        "actions": [],  # Empty actions
        "dmx": []
    }
    result = translator.run(empty_actions_state)
    print(f"✓ Handled gracefully: {len(result['dmx'])} DMX commands")


if __name__ == "__main__":
    print("🚀 LangGraph Agent Examples & Testing")
    print("=====================================")
    
    try:
        # Test individual agents
        final_result = test_individual_agents()
        
        # Test partial execution
        partial_result = test_partial_pipeline()
        
        # Test error handling
        demonstrate_error_handling()
        
        print("\n✅ All agent tests completed successfully!")
        print("\n📝 Key Benefits of Modular Agents:")
        print("  • Independent testing and debugging")
        print("  • Flexible model configuration per agent") 
        print("  • Easy to extend with new agent types")
        print("  • Reusable across different pipelines")
        print("  • Better error isolation and handling")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
