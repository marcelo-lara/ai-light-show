"""
Lighting Pipeline for AI-based Lighting Design

This module provides a simple sequential pipeline for processing lighting designs.
"""
import json
from typing import Dict, Any, Optional, List
from typing_extensions import TypedDict
from pathlib import Path

from .agents import ContextBuilderAgent, LightingPlannerAgent, EffectTranslatorAgent


class PipelineState(TypedDict):
    segment: Dict[str, Any]
    context_summary: str
    actions: list
    dmx: list


def save_node_output(node_name: str, data: Any) -> None:
    """Save node output to logs for debugging"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    output_file = logs_dir / f"{node_name}.json"
    try:
        data_dict = dict(data) if hasattr(data, 'keys') else data
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=2)
        print(f"💾 Saved {node_name} output to {output_file}")
    except Exception as e:
        print(f"⚠️ Failed to save {node_name} output: {e}")


def run_lighting_pipeline(segment_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete lighting pipeline on a segment
    
    Args:
        segment_input: Dictionary containing segment information
        
    Returns:
        Complete pipeline result with DMX commands
    """
    print("🚀 Starting Lighting Pipeline...")
    
    try:
        # Initialize state
        state: PipelineState = {
            "segment": segment_input.get("segment", {}),
            "context_summary": "",
            "actions": [],
            "dmx": []
        }
        
        # Run nodes sequentially
        print("  → Running context builder...")
        context_builder = ContextBuilderAgent()
        state = context_builder.run(state)
        
        print("  → Running lighting planner...")
        lighting_planner = LightingPlannerAgent()
        state = lighting_planner.run(state)
        
        print("  → Running effect translator...")
        effect_translator = EffectTranslatorAgent()
        state = effect_translator.run(state)
        
        print("✅ Pipeline completed successfully!")
        
        # Save complete result
        save_node_output("pipeline_complete", state)
        
        return dict(state)
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        return {
            "segment": segment_input.get("segment", {}),
            "context_summary": f"Pipeline error: {str(e)}",
            "actions": [],
            "dmx": []
        }


# Test function
def test_lighting_pipeline():
    """Test the lighting pipeline with a sample segment"""
    test_segment = {
        "segment": {
            "name": "Drop",
            "start": 60.0,
            "end": 75.0,
            "features": {
                "energy": 0.9,
                "intensity": "high",
                "mood": "energetic"
            }
        }
    }
    
    print("🧪 Running pipeline test...")
    result = run_lighting_pipeline(test_segment)
    print(json.dumps(result, indent=2))
    return result


# Allow running as a script for testing
if __name__ == "__main__":
    test_lighting_pipeline()
