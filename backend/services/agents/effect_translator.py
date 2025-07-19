"""
Effect Translator Agent - Unified Implementation
Combines functionality from both LangGraph and Ollama implementations
"""
import json
import re
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from pathlib import Path

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


class EffectTranslatorAgent:
    """
    Unified Effect Translator Agent
    - For LangGraph Pipeline: Converts symbolic lighting actions into standardized direct commands
    - For Direct Commands: Simple effect translation interface
    """
    
    def __init__(self, model: str = "command-r", fallback_model: str = "mixtral"):
        self.model = model
        self.fallback_model = fallback_model
    
    def _get_dynamic_fixture_info(self) -> Dict[str, Any]:
        """Get dynamic fixture information from the global app_state"""
        try:
            from ...models.app_state import app_state
            
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
        except ImportError:
            # Fallback to hardcoded values if app_state not available
            return {
                'fixture_ids': ['head_el150', 'parcan_l', 'parcan_r', 'parcan_pl', 'parcan_pr'],
                'channels': ['red', 'green', 'blue', 'white', 'dim', 'dimmer', 'pan', 'tilt', 'color', 'gobo', 'shutter'],
                'presets': ['Drop', 'Flash', 'Strobe', 'Home', 'Piano']
            }
    
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the effect translation process for LangGraph pipeline"""
        print("🎛️ Running Effect Translator...")
        
        actions = state.get("actions", [])
        
        if not actions:
            print("⚠️ No actions to translate")
            result_state = state.copy()
            result_state["dmx"] = []
            return result_state
        
        # Get dynamic fixture information for context
        fixture_info = self._get_dynamic_fixture_info()
        
        # Build prompt for effect translation
        prompt = self._build_prompt(actions, fixture_info)
        
        try:
            # Call model via Ollama with fallback
            response = self._query_model(prompt)
            
            # Parse direct command strings from response
            dmx_commands = self._parse_dmx_commands(response, actions)
            
            # Update state
            result_state = state.copy()
            result_state["dmx"] = dmx_commands
            
            # Save output for debugging
            save_node_output("effect_translator", {
                "input": {
                    "actions": actions,
                    "fixture_info": fixture_info
                },
                "dmx_commands": dmx_commands,
                "model_response": response
            })
            
            print(f"✅ Generated {len(dmx_commands)} DMX commands")
            return result_state
            
        except Exception as e:
            print(f"❌ Effect Translator failed: {e}")
            # Create fallback commands
            fallback_commands = self._create_fallback_commands(actions)
            result_state = state.copy()
            result_state["dmx"] = fallback_commands
            return result_state
    
    def _build_prompt(self, actions: List[Dict[str, Any]], fixture_info: Dict[str, Any]) -> str:
        """Build the prompt for effect translation"""
        fixture_ids = fixture_info.get('fixture_ids', [])
        channels = fixture_info.get('channels', [])
        presets = fixture_info.get('presets', [])
        
        primary_fixture = fixture_ids[0] if fixture_ids else 'parcan_l'
        secondary_fixture = fixture_ids[1] if len(fixture_ids) > 1 else primary_fixture
        
        return f"""You are a DMX lighting console operator.

Convert these symbolic lighting actions into direct commands:
{json.dumps(actions, indent=2)}

Available fixtures: {fixture_ids}
Available channels: {channels}
Available presets: {presets}

Use direct command syntax like:
- "#set fixture_id channel to value at time"
- "#fade fixture_id channel from start_value to end_value duration seconds"
- "#preset fixture_id preset_name at time"
- "#strobe fixture_id channel rate hz duration seconds"

Examples:
- "flash" action → #set fixture dim to 1.0 at start_time, then #set fixture dim to 0.0 at start_time+duration
- "strobe" action → #strobe fixture dim rate 10 duration duration_seconds
- "fade" action → #fade fixture dim from 0.0 to 1.0 duration duration_seconds
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
            action_type = action.get("type", action.get("action", "flash"))
            
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

    # Legacy methods for backward compatibility
    def translate_effect(self, prompt: str, **kwargs):
        """Legacy method for simple effect translation"""
        response = query_ollama(prompt, model=self.model, **kwargs)
        return self.parse_response(response)

    def parse_response(self, response):
        """Simple response parsing for backward compatibility"""
        return response


# Node function for LangGraph compatibility
def run_effect_translator(state: PipelineState) -> PipelineState:
    """LangGraph-compatible node function"""
    agent = EffectTranslatorAgent()
    return agent.run(state)
