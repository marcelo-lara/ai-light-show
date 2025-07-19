"""
Effect Translator Agent - Node 3 of the Lighting Pipeline
Converts symbolic lighting actions into DMX fixture instructions
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


class EffectTranslatorAgent:
    """
    Agent 3: Effect Translator (Command-R)
    Converts symbolic lighting actions into DMX fixture instructions
    """
    
    def __init__(self, model: str = "command-r", fallback_model: str = "mixtral"):
        self.model = model
        self.fallback_model = fallback_model
    
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the effect translation process"""
        print("🎛️ Running Effect Translator...")
        
        actions = state.get("actions", [])
        
        if not actions:
            print("⚠️ No actions to translate")
            result_state = state.copy()
            result_state["dmx"] = []
            return result_state
        
        # Build prompt for DMX translation
        prompt = self._build_prompt(actions)
        
        try:
            # Call Command-R model via Ollama (fallback to mixtral if command-r not available)
            response = self._query_model(prompt)
            
            # Extract and parse DMX commands from response
            dmx_commands = self._parse_dmx_commands(response, actions)
            
            # Update state
            result_state = state.copy()
            result_state["dmx"] = dmx_commands
            
            # Save output for debugging
            save_node_output("effect_translator", {
                "input": actions,
                "dmx": dmx_commands,
                "model_response": response
            })
            
            print(f"✅ Generated {len(dmx_commands)} DMX commands")
            return result_state
            
        except Exception as e:
            print(f"❌ Effect Translator failed: {e}")
            result_state = state.copy()
            result_state["dmx"] = []
            return result_state
    
    def _build_prompt(self, actions: List[Dict[str, Any]]) -> str:
        """Build the prompt for DMX translation"""
        actions_json = json.dumps(actions, indent=2)
        
        return f"""You are a lighting control expert.

Given a list of symbolic lighting actions like:
{actions_json}

Convert these into low-level DMX fixture instructions for:
- Fixture: "parcan_l" uses channel 10 for color/strobe (255=on, 0=off)
- Fixture: "parcan_r" uses channel 11 for color/strobe (255=on, 0=off)  
- Fixture: "head_el150" uses presets like "Drop", "Flash", "Strobe"

For each action, create appropriate DMX commands:
- "flash" → set channel to 255 for duration then 0
- "strobe" → set channel to 255 with strobe preset
- "fade" → gradual transition from 0 to 255
- "pulse" → quick on/off pattern

Output JSON with a "dmx" array:
[
  {{"fixture": "parcan_l", "channel": 10, "value": 255, "time": 34.2}},
  {{"fixture": "parcan_l", "channel": 10, "value": 0, "time": 36.7}},
  {{"fixture": "head_el150", "preset": "Drop", "time": 35.0}}
]

Return ONLY valid JSON."""
    
    def _query_model(self, prompt: str) -> str:
        """Query the model with fallback support"""
        try:
            return query_ollama(prompt, model=self.model)
        except:
            print(f"⚠️ {self.model} not available, using {self.fallback_model}")
            return query_ollama(prompt, model=self.fallback_model)
    
    def _parse_dmx_commands(self, response: str, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse DMX commands from LLM response"""
        dmx_commands = []
        
        try:
            # Try to parse JSON directly
            if response.strip().startswith('['):
                dmx_commands = json.loads(response.strip())
            else:
                # Look for JSON in response
                json_match = re.search(r'\[[\s\S]*?\]', response)
                if json_match:
                    dmx_commands = json.loads(json_match.group(0))
                else:
                    # Fallback: create basic DMX commands
                    dmx_commands = self._create_fallback_dmx(actions)
        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse JSON from effect translator: {response}")
            # Fallback DMX commands
            dmx_commands = self._create_fallback_dmx(actions)
        
        return dmx_commands
    
    def _create_fallback_dmx(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create fallback DMX commands when parsing fails"""
        dmx_commands = []
        
        for action in actions:
            # Basic on command
            dmx_commands.append({
                "fixture": "parcan_l",
                "channel": 10,
                "value": 255,
                "time": action.get("start", 0)
            })
            # Basic off command
            dmx_commands.append({
                "fixture": "parcan_l", 
                "channel": 10,
                "value": 0,
                "time": action.get("start", 0) + action.get("duration", 1)
            })
        
        return dmx_commands


# Node function for LangGraph compatibility
def run_effect_translator(state: PipelineState) -> PipelineState:
    """LangGraph-compatible node function"""
    agent = EffectTranslatorAgent()
    return agent.run(state)
