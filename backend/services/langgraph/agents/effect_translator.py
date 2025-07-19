"""
Effect Translator Agent - Node 3 of the Lighting Pipeline
Converts symbolic lighting actions into standardized direct commands
"""
import json
import re
from typing import Dict, Any, List, Optional
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
    
    def _get_dynamic_fixture_info(self) -> Dict[str, Any]:
        """Get dynamic fixture information from the global app_state"""
        from backend.models.app_state import app_state
        
        if not app_state.fixtures:
            # Fallback to hardcoded values if fixtures not loaded
            return {
                'fixture_ids': ['head_el150', 'parcan_l', 'parcan_r', 'parcan_pl', 'parcan_pr'],
                'channels': ['red', 'green', 'blue', 'white', 'dim', 'dimmer', 'pan', 'tilt', 'color', 'gobo', 'shutter'],
                'presets': ['Drop', 'Flash', 'Strobe', 'Home', 'Piano']
            }
        
        fixture_ids = list(app_state.fixtures.fixtures.keys())
        
        # Get all available channels from all fixtures
        channels = set()
        presets = set()
        fixture_types = {}
        
        for fixture_id, fixture in app_state.fixtures.fixtures.items():
            # Get fixture type
            fixture_types[fixture_id] = fixture.fixture_type
            
            # Get channels from fixture's _config
            if hasattr(fixture, '_config') and fixture._config and 'channels' in fixture._config:
                channels.update(fixture._config['channels'].keys())
            
            # Get presets from fixture's _config
            if hasattr(fixture, '_config') and fixture._config and 'presets' in fixture._config:
                for preset in fixture._config['presets']:
                    if isinstance(preset, dict) and 'name' in preset:
                        presets.add(preset['name'])
        
        # Add common channels if none found
        if not channels:
            channels = {'red', 'green', 'blue', 'white', 'dim', 'dimmer', 'pan', 'tilt', 'color', 'gobo', 'shutter'}
        
        # Add common presets if none found
        if not presets:
            presets = {'Drop', 'Flash', 'Strobe', 'Home', 'Piano'}
        
        return {
            'fixture_ids': fixture_ids,
            'channels': sorted(list(channels)),
            'presets': sorted(list(presets)),
            'fixture_types': fixture_types
        }
    
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
        """Build the prompt for direct command translation using dynamic fixture information"""
        actions_json = json.dumps(actions, indent=2)
        
        # Get dynamic fixture information
        fixture_info = self._get_dynamic_fixture_info()
        fixture_ids = fixture_info['fixture_ids']
        channels = fixture_info['channels']
        presets = fixture_info['presets']
        
        # Create examples using available fixtures
        primary_fixture = fixture_ids[0] if fixture_ids else 'fixture_1'
        secondary_fixture = fixture_ids[1] if len(fixture_ids) > 1 else fixture_ids[0] if fixture_ids else 'fixture_2'
        
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

CURRENT VENUE CONFIGURATION:
- Available Fixtures: {', '.join(fixture_ids)}
- Available Channels: {', '.join(channels)}
- Available Presets: {', '.join(presets)}

RULES:
- Channel values must be normalized between 0.0 and 1.0 (0.0 = DMX 0, 1.0 = DMX 255)
- Use ONLY the fixtures listed above: {', '.join(fixture_ids)}
- Use ONLY the channels listed above: {', '.join(channels)}
- Use ONLY the presets listed above: {', '.join(presets)}
- Times are in seconds (decimal allowed)

MAPPING GUIDELINES:
- "flash" action → #set fixture dim to 1.0 at start_time, then #set fixture dim to 0.0 at end_time
- "strobe" action → #strobe fixture dim rate 10 duration <duration>
- "fade" action → #fade fixture dim from 0.0 to 1.0 duration <duration>
- "pulse" action → #set fixture dim to 1.0 at start_time, then #set fixture dim to 0.0 at start_time+0.1

Output as JSON array of command strings:
[
  "#set {primary_fixture} dim to 1.0 at 34.2",
  "#set {primary_fixture} dim to 0.0 at 36.7",
  "#preset {secondary_fixture} {presets[0] if presets else 'Drop'} at 35.0"
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
        """Create fallback direct commands when parsing fails using dynamic fixture information"""
        commands = []
        
        # Get dynamic fixture information
        fixture_info = self._get_dynamic_fixture_info()
        fixture_ids = fixture_info['fixture_ids']
        
        # Use first available fixture for fallback
        fallback_fixture = fixture_ids[0] if fixture_ids else 'parcan_l'
        
        for action in actions:
            start_time = action.get("start", 0)
            duration = action.get("duration", 1)
            action_type = action.get("action", "flash")
            
            # Create basic direct commands based on action type
            if action_type == "flash":
                commands.append(f"#set {fallback_fixture} dim to 1.0 at {start_time}")
                commands.append(f"#set {fallback_fixture} dim to 0.0 at {start_time + duration}")
            elif action_type == "strobe":
                commands.append(f"#strobe {fallback_fixture} dim rate 10 duration {duration}")
            elif action_type == "fade":
                commands.append(f"#fade {fallback_fixture} dim from 0.0 to 1.0 duration {duration}")
            else:
                # Default to flash
                commands.append(f"#set {fallback_fixture} dim to 1.0 at {start_time}")
                commands.append(f"#set {fallback_fixture} dim to 0.0 at {start_time + duration}")
        
        return commands


# Node function for LangGraph compatibility
def run_effect_translator(state: PipelineState) -> PipelineState:
    """LangGraph-compatible node function"""
    agent = EffectTranslatorAgent()
    return agent.run(state)
