"""
Lighting Planner Agent

This agent proposes symbolic lighting actions based on context summaries.
"""
import json
import re
from typing import Dict, Any, List
from typing_extensions import TypedDict
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from ..ollama.ollama_api import query_ollama


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
    Lighting Planner Agent
    
    Proposes symbolic lighting actions based on context summaries and musical segments.
    Provides a simple interface for lighting planning.
    """
    
    def __init__(self, model: str = "mixtral"):
        self.model = model
        # Setup Jinja2 environment
        self.prompts_dir = Path(__file__).parent / "prompts"
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.prompts_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the lighting planning process for the pipeline"""
        print("💡 Running Lighting Planner...")
        
        context_summary = state.get("context_summary", "")
        segment = state.get("segment", {})
        
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        duration = end_time - start_time
        
        # Build prompt using Jinja2 template
        prompt = self._build_prompt(context_summary, segment)
        
        try:
            # Call model via Ollama
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
    
    def _build_prompt(self, context_summary: str, segment: Dict[str, Any]) -> str:
        """Build the prompt using Jinja2 template"""
        # Get fixtures from app_state
        from backend.models.app_state import app_state
        
        # Get current song from app_state
        song = app_state.current_song if app_state.current_song else None
        
        # Prepare fixtures data for template
        fixtures_data = []
        if app_state.fixtures:
            for fixture_id, fixture in app_state.fixtures.fixtures.items():
                fixtures_data.append({
                    'id': fixture_id,
                    'type': getattr(fixture, 'type', 'Unknown'),
                    'effects': getattr(fixture, 'effects', ['flash', 'fade'])
                })
        
        # Calculate segment duration
        start_time = segment.get("start", 0.0)
        end_time = segment.get("end", 0.0)
        duration = end_time - start_time
        
        # Add calculated duration to segment data
        segment_with_duration = segment.copy()
        segment_with_duration['duration'] = duration
        
        # Render template
        template = self.jinja_env.get_template('lighting_planner.prompt.j2')
        prompt = template.render(
            song=song,
            fixtures=fixtures_data,
            context_summary=context_summary,
            segment=segment_with_duration
        )
        
        return prompt
    
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
