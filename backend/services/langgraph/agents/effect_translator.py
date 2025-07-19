"""
Effect Translator Agent - Node 3 of the Lighting Pipeline
Converts symbolic lighting actions into standardized direct commands
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
    Converts symbolic lighting actions into standardized direct commands
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
            
            # Extract and parse direct commands from response
            direct_commands = self._parse_dmx_commands(response, actions)
            
            # Update state
            result_state = state.copy()
            result_state["dmx"] = direct_commands
            
            # Save output for debugging
            save_node_output("effect_translator", {
                "input": actions,
                "direct_commands": direct_commands,
                "model_response": response
            })
            
            print(f"✅ Generated {len(direct_commands)} direct commands")
            return result_state
            
        except Exception as e:
            print(f"❌ Effect Translator failed: {e}")
            result_state = state.copy()
            result_state["dmx"] = []
            return result_state
    
    def _build_prompt(self, actions: List[Dict[str, Any]]) -> str:
        """Build the prompt for direct command translation"""
        actions_json = json.dumps(actions, indent=2)
        
        return f"""You are a lighting control expert tasked with converting symbolic lighting actions into standardized direct commands.

Given these symbolic lighting actions:
{actions_json}

Convert them into ONLY the following standardized direct commands (do NOT create custom DMX instructions):

AVAILABLE DIRECT COMMANDS:
1. Set Channel: #set <fixture> <channel_name> to <value> at <time>
2. Preset: #preset <fixture> <preset_name> at <time>
3. Fade Channel: #fade <fixture> <channel_name> from <start_value> to <end_value> duration <time>
4. Strobe Channel: #strobe <fixture> <channel_name> rate <frequency> duration <time>
5. Clear State: #clear <fixture> state at <time>

RULES:
- Channel values must be normalized between 0.0 and 1.0 (0.0 = DMX 0, 1.0 = DMX 255)
- Use only fixtures: parcan_l, parcan_r, head_el150
- Use only channels: red, green, blue, white, dimmer
- Use only presets: Drop, Flash, Strobe, Home
- Times are in seconds (decimal allowed)

MAPPING GUIDELINES:
- "flash" action → #set fixture dimmer to 1.0 at start_time, then #set fixture dimmer to 0.0 at end_time
- "strobe" action → #strobe fixture dimmer rate 10 duration <duration>
- "fade" action → #fade fixture dimmer from 0.0 to 1.0 duration <duration>
- "pulse" action → #set fixture dimmer to 1.0 at start_time, then #set fixture dimmer to 0.0 at start_time+0.1

Output as JSON array of command strings:
[
  "#set parcan_l dimmer to 1.0 at 34.2",
  "#set parcan_l dimmer to 0.0 at 36.7",
  "#preset head_el150 Drop at 35.0"
]

Return ONLY valid JSON array of command strings."""
    
    def _query_model(self, prompt: str) -> str:
        """Query the model with fallback support"""
        try:
            return query_ollama(prompt, model=self.model)
        except:
            print(f"⚠️ {self.model} not available, using {self.fallback_model}")
            return query_ollama(prompt, model=self.fallback_model)
    
    def _parse_dmx_commands(self, response: str, actions: List[Dict[str, Any]]) -> List[str]:
        """Parse direct command strings from LLM response"""
        commands = []
        
        try:
            # Try to parse JSON directly
            if response.strip().startswith('['):
                commands = json.loads(response.strip())
            else:
                # Look for JSON in response
                json_match = re.search(r'\[[\s\S]*?\]', response)
                if json_match:
                    commands = json.loads(json_match.group(0))
                else:
                    # Fallback: create basic direct commands
                    commands = self._create_fallback_commands(actions)
                    
            # Ensure all commands are strings and start with #
            validated_commands = []
            for cmd in commands:
                if isinstance(cmd, str) and cmd.strip().startswith('#'):
                    validated_commands.append(cmd.strip())
                elif isinstance(cmd, str):
                    validated_commands.append(f"#{cmd.strip()}")
                    
            return validated_commands
            
        except json.JSONDecodeError:
            print(f"⚠️ Failed to parse JSON from effect translator: {response}")
            # Fallback direct commands
            return self._create_fallback_commands(actions)
    
    def _create_fallback_commands(self, actions: List[Dict[str, Any]]) -> List[str]:
        """Create fallback direct commands when parsing fails"""
        commands = []
        
        for action in actions:
            start_time = action.get("start", 0)
            duration = action.get("duration", 1)
            action_type = action.get("action", "flash")
            
            # Create basic direct commands based on action type
            if action_type == "flash":
                commands.append(f"#set parcan_l dimmer to 1.0 at {start_time}")
                commands.append(f"#set parcan_l dimmer to 0.0 at {start_time + duration}")
            elif action_type == "strobe":
                commands.append(f"#strobe parcan_l dimmer rate 10 duration {duration}")
            elif action_type == "fade":
                commands.append(f"#fade parcan_l dimmer from 0.0 to 1.0 duration {duration}")
            else:
                # Default to flash
                commands.append(f"#set parcan_l dimmer to 1.0 at {start_time}")
                commands.append(f"#set parcan_l dimmer to 0.0 at {start_time + duration}")
        
        return commands


# Node function for LangGraph compatibility
def run_effect_translator(state: PipelineState) -> PipelineState:
    """LangGraph-compatible node function"""
    agent = EffectTranslatorAgent()
    return agent.run(state)
