"""
LangGraph Pipeline for AI-based Lighting Design
3-Agent Chain: Context Builder → Lighting Planner → Effect Translator
"""
import json
import os
from typing import Dict, Any, Union
from typing_extensions import TypedDict
from pathlib import Path

# Define PipelineState outside try block so it's always available
class PipelineState(TypedDict):
    segment: Dict[str, Any]
    context_summary: str
    actions: list
    dmx: list

# Try to import LangGraph, but provide fallback if not available
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
        
except ImportError:
    print("Info: LangGraph not installed. Pipeline will run in fallback mode.")
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = "__end__"

# Import agents from unified location
from ..agents.context_builder import ContextBuilderAgent, run_context_builder
from ..agents.lighting_planner import LightingPlannerAgent, run_lighting_planner  
from ..agents.effect_translator import EffectTranslatorAgent, run_effect_translator


def save_node_output(node_name: str, data: Union[Dict[str, Any], PipelineState]) -> None:
    """Save node output to logs for debugging"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    output_file = logs_dir / f"{node_name}.json"
    try:
        # Convert TypedDict to regular dict if needed
        data_dict = dict(data) if hasattr(data, '__dict__') or hasattr(data, 'keys') else data
        with open(output_file, 'w') as f:
            json.dump(data_dict, f, indent=2)
        print(f"💾 Saved {node_name} output to {output_file}")
    except Exception as e:
        print(f"⚠️ Failed to save {node_name} output: {e}")


def create_lighting_pipeline():
    """Create and configure the LangGraph pipeline"""
    
    if not LANGGRAPH_AVAILABLE or StateGraph is None:
        print("⚠️ LangGraph not available, pipeline will use fallback mode")
        return None
    
    try:
        # Create state graph 
        workflow = StateGraph(PipelineState)
        
        # Add nodes
        workflow.add_node("context_builder", run_context_builder)
        workflow.add_node("lighting_planner", run_lighting_planner)
        workflow.add_node("effect_translator", run_effect_translator)
        
        # Set entry point
        workflow.set_entry_point("context_builder")
        
        # Add edges (chain the nodes)
        workflow.add_edge("context_builder", "lighting_planner")
        workflow.add_edge("lighting_planner", "effect_translator")
        workflow.add_edge("effect_translator", END)
        
        # Compile the workflow
        return workflow.compile()
    except Exception as e:
        print(f"⚠️ Failed to create LangGraph pipeline: {e}")
        return None


def run_lighting_pipeline(segment_input: Dict[str, Any]) -> Union[Dict[str, Any], PipelineState]:
    """
    Run the complete lighting pipeline on a segment
    
    Args:
        segment_input: Dictionary containing segment information
        
    Returns:
        Complete pipeline result with DMX commands
    """
    print("🚀 Starting Lighting Pipeline...")
    
    try:
        # Try LangGraph pipeline first
        if LANGGRAPH_AVAILABLE:
            try:
                pipeline = create_lighting_pipeline()
                if pipeline is not None:
                    # Prepare input for LangGraph
                    pipeline_input: PipelineState = {
                        "segment": segment_input.get("segment", {}),
                        "context_summary": "",
                        "actions": [],
                        "dmx": []
                    }
                    
                    result = pipeline.invoke(pipeline_input)
                    print("✅ LangGraph pipeline completed successfully!")
                    save_node_output("pipeline_complete", result)
                    return dict(result) if hasattr(result, 'keys') else result
            except Exception as e:
                print(f"⚠️ LangGraph pipeline failed: {e}, falling back to sequential mode")
        
        # Fallback: Run nodes sequentially without LangGraph
        print("🔄 Running pipeline in sequential fallback mode")
        
        # Initialize state
        state: PipelineState = {
            "segment": segment_input.get("segment", {}),
            "context_summary": "",
            "actions": [],
            "dmx": []
        }
        
        # Run nodes sequentially
        print("  → Running context builder...")
        state = run_context_builder(state)
        
        print("  → Running lighting planner...")
        state = run_lighting_planner(state) 
        
        print("  → Running effect translator...")
        state = run_effect_translator(state)
        
        print("✅ Sequential pipeline completed successfully!")
        
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
    """Test the lighting pipeline with sample data"""
    
    test_segment = {
        "segment": {
            "name": "Drop",
            "start": 34.2,
            "end": 36.7,
            "features": {
                "bpm": 128,
                "energy": 0.92,
                "instrumentation": ["kick", "bass", "synth"]
            }
        }
    }
    
    print("🧪 Testing Lighting Pipeline...")
    result = run_lighting_pipeline(test_segment)
    
    print("\n📊 Pipeline Results:")
    print(f"Context: {result.get('context_summary', 'N/A')}")
    print(f"Actions: {len(result.get('actions', []))} lighting actions")
    print(f"DMX Commands: {len(result.get('dmx', []))} commands")
    
    return result


if __name__ == "__main__":
    # Run test when script is executed directly
    test_lighting_pipeline()
