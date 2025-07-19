"""
Context Builder Agent - Node 1 of the Lighting Pipeline
Interprets musical segments and generates natural language context summaries
"""
import json
from typing import Dict, Any
from typing_extensions import TypedDict
from pathlib import Path

from ...ollama.ollama_api import query_ollama


class PipelineState(TypedDict):
    segment: Dict[str, Any]
    context_summary: str
    actions: list
    dmx: list


def save_node_output(node_name: str, data: Dict[str, Any]) -> None:
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


class ContextBuilderAgent:
    """
    Agent 1: Context Builder (Mixtral)
    Interprets the musical segment and generates a natural language context summary
    """
    
    def __init__(self, model: str = "mixtral"):
        self.model = model
    
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the context building process"""
        print("🎵 Running Context Builder...")
        
        segment = state.get("segment", {})
        
        # Extract segment information
        name = segment.get("name", "Unknown")
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        features = segment.get("features", {})
        
        # Build prompt for context interpretation
        prompt = self._build_prompt(name, start_time, end_time, features)
        
        try:
            # Call Mixtral model via Ollama
            response = query_ollama(prompt, model=self.model)
            
            # Extract context summary from response
            context_summary = response.strip().strip('"')
            
            # Update state
            result_state = state.copy()
            result_state["context_summary"] = context_summary
            
            # Save output for debugging
            save_node_output("context_builder", {
                "input": segment,
                "context_summary": context_summary,
                "model_response": response
            })
            
            print(f"✅ Context: {context_summary}")
            return result_state
            
        except Exception as e:
            print(f"❌ Context Builder failed: {e}")
            result_state = state.copy()
            result_state["context_summary"] = f"Error processing segment: {str(e)}"
            return result_state
    
    def _build_prompt(self, name: str, start_time: float, end_time: float, features: Dict[str, Any]) -> str:
        """Build the prompt for context interpretation"""
        return f"""You are a music context interpreter.
Describe the emotional and sonic feel of this section:

Segment: {name}
Start: {start_time}s
End: {end_time}s
Features: {json.dumps(features)}

Respond with a short natural language summary like:
"High energy climax with heavy bass and bright synth"

Focus on the mood, energy level, and key instruments. Keep it concise and descriptive."""


# Node function for LangGraph compatibility
def run_context_builder(state: PipelineState) -> PipelineState:
    """LangGraph-compatible node function"""
    agent = ContextBuilderAgent()
    return agent.run(state)
