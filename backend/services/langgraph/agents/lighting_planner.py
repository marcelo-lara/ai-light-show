"""
Lighting Planner Agent - Node 2 of the Lighting Pipeline
Proposes symbolic lighting actions based on context summaries
"""
import json
import re
from typing import Dict, Any, List
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


class LightingPlannerAgent:
    """
    Agent 2: Lighting Planner (Mixtral)
    Proposes symbolic lighting actions based on the context summary
    """
    
    def __init__(self, model: str = "mixtral"):
        self.model = model
    
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the lighting planning process"""
        print("💡 Running Lighting Planner...")
        
        context_summary = state.get("context_summary", "")
        segment = state.get("segment", {})
        
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        duration = end_time - start_time
        
        # Build prompt for lighting planning
        prompt = self._build_prompt(context_summary, start_time, end_time, duration)
        
        try:
            # Call Mixtral model via Ollama
            response = query_ollama(prompt, model=self.model)
            
            # Extract and parse actions from response
            actions = self._parse_actions(response, start_time, duration)
            
            # Update state
            result_state = state.copy()
            result_state["actions"] = actions
            
            # Save output for debugging
            save_node_output("lighting_planner", {
                "input": {
                    "context_summary": context_summary,
                    "segment": segment
                },
                "actions": actions,
                "model_response": response
            })
            
            print(f"✅ Generated {len(actions)} lighting actions")
            return result_state
            
        except Exception as e:
            print(f"❌ Lighting Planner failed: {e}")
            result_state = state.copy()
            result_state["actions"] = []
            return result_state
    
    def _build_prompt(self, context_summary: str, start_time: float, end_time: float, duration: float) -> str:
        """Build the prompt for lighting planning"""
        return f"""You are a stage lighting designer.

Based on this musical context:
"{context_summary}"

Suggest lighting actions. Use "flash", "strobe", "fade", "pulse", "sweep" etc.
Return JSON array with:
- type (lighting action type)
- color (color name)
- start (seconds from segment start)
- duration (seconds)

This section starts at: {start_time}s and ends at: {end_time}s (duration: {duration:.1f}s)

Return ONLY valid JSON in this format:
[
  {{"type": "strobe", "color": "white", "start": {start_time}, "duration": 2.5}},
  {{"type": "flash", "color": "blue", "start": {start_time + 1.0}, "duration": 1.0}}
]"""
    
    def _parse_actions(self, response: str, start_time: float, duration: float) -> List[Dict[str, Any]]:
        """Parse lighting actions from LLM response"""
        actions = []
        
        try:
            # Try to parse JSON directly
            if response.strip().startswith('['):
                actions = json.loads(response.strip())
            else:
                # Look for JSON in response
                json_match = re.search(r'\[[\s\S]*\]', response)
                if json_match:
                    actions = json.loads(json_match.group(0))
                else:
                    # Fallback: create basic actions
                    actions = [
                        {
                            "type": "flash",
                            "color": "white",
                            "start": start_time,
                            "duration": duration
                        }
                    ]
        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse JSON from lighting planner: {response}")
            # Fallback actions
            actions = [
                {
                    "type": "fade",
                    "color": "auto",
                    "start": start_time,
                    "duration": duration
                }
            ]
        
        return actions


# Node function for LangGraph compatibility
def run_lighting_planner(state: PipelineState) -> PipelineState:
    """LangGraph-compatible node function"""
    agent = LightingPlannerAgent()
    return agent.run(state)
