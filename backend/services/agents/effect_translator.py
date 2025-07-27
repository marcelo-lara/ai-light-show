"""
Effect Translator Agent

This agent converts symbolic lighting actions into standardized direct commands.
"""
import json
import re
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from config import LOGS_DIR
from pathlib import Path

from ..ollama.ollama_api import query_ollama


class PipelineState(TypedDict):
    segment: Dict[str, Any]
    context_summary: str
    actions: list
    dmx: list


def save_node_output(node_name: str, data: Dict[str, Any]) -> None:
    """Save node output to logs for debugging"""
    logs_dir = LOGS_DIR
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
    Effect Translator Agent
    
    Converts symbolic lighting actions into standardized direct commands.
    Provides a simple interface for effect translation.
    """
    
    def __init__(self, model: str = "command-r", fallback_model: str = "mistral"):
        self.model = model
        self.fallback_model = fallback_model
    
    def _get_dynamic_fixture_info(self) -> Dict[str, Any]:
        """Get dynamic fixture information from the global app_state"""
        try:
            from ...models.app_state import app_state
            
            if not app_state.fixtures:
                raise ValueError("☠️ Fixtures not loaded in app_state")
            
            fixture_ids = list(app_state.fixtures.fixtures.keys())
            
            # Get all available channels from all fixtures
            channels = set()
            actions = set()
            fixture_types = {}
            
            for fixture_id, fixture in app_state.fixtures.fixtures.items():
                # Get fixture type
                fixture_types[fixture_id] = fixture.fixture_type
                
                # Get channels from fixture's _config
                if hasattr(fixture, '_config') and fixture._config and 'channels' in fixture._config:
                    channels.update(fixture._config['channels'].keys())
                
                # Get actions from fixture's _config
                if hasattr(fixture, '_config') and fixture._config and 'actions' in fixture._config:
                    for preset in fixture._config['actions']:
                        if isinstance(preset, dict) and 'name' in preset:
                            actions.add(preset['name'])
            
            # Add common channels if none found
            if not channels:
                raise ValueError("☠️ Fixtures channels not loaded")
            
            # Add common actions if none found
            if not actions:
                raise ValueError("☠️ Fixtures actions not loaded")

            return {
                'fixture_ids': fixture_ids,
                'channels': sorted(list(channels)),
                'actions': sorted(list(actions)),
                'fixture_types': fixture_types
            }
        except ImportError:
            raise ValueError("☠️ Import error: Ensure app_state and fixtures are loaded")

    
    def run(self, state: PipelineState) -> PipelineState:
        """Execute the effect translation process for the pipeline"""
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
            result_state = state.copy()
            return result_state
    
    def _build_prompt(self, actions: List[Dict[str, Any]], fixture_info: Dict[str, Any]) -> str:
        """Build the prompt for effect translation"""
        fixture_ids = fixture_info.get('fixture_ids', [])
        channels = fixture_info.get('channels', [])
        actions = fixture_info.get('actions', [])
        
        primary_fixture = fixture_ids[0] if fixture_ids else 'parcan_l'
        secondary_fixture = fixture_ids[1] if len(fixture_ids) > 1 else primary_fixture
        
        # Setup Jinja2 environment (lazy initialization)
        if not hasattr(self, 'jinja_env'):
            from jinja2 import Environment, FileSystemLoader
            self.prompts_dir = Path(__file__).parent / "prompts"
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.prompts_dir),
                trim_blocks=True,
                lstrip_blocks=True
            )
        
        # Render template
        template = self.jinja_env.get_template('effect_translator.j2')
        prompt = template.render(
            actions=actions,
            fixture_ids=fixture_ids,
            channels=channels,
            primary_fixture=primary_fixture,
            secondary_fixture=secondary_fixture
        )
        
        return prompt
    
    def _query_model(self, prompt: str) -> str:
        """Query the model"""
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
                    print("⚠️ No JSON found in response.")

            # Ensure all commands are strings and start with #
            validated_commands = []
            for cmd in commands:
                if isinstance(cmd, str) and cmd.strip().startswith('#'):
                    validated_commands.append(cmd.strip())
                elif isinstance(cmd, str):
                    validated_commands.append(f"#{cmd.strip()}")
                    
            return validated_commands
            
        except json.JSONDecodeError:
            print(f"☠️☠️ Failed to parse JSON from effect translator: {response}")
            return []


# Helper function for backward compatibility
def run_effect_translator(state: PipelineState) -> PipelineState:
    """Run effect translator on a pipeline state"""
    agent = EffectTranslatorAgent()
    return agent.run(state)
