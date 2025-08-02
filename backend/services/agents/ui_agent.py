"""
UI Agent

This agent routes user intentions to the appropriate agents to fulfill their requests.
"""

from typing import Optional, Dict, Any, Callable
from datetime import datetime
from ._agent_model import AgentModel

class UIAgent(AgentModel):
    """
    UI Agent model that handles user requests and provides lighting control responses.
    This is the main agent that replaces the ai_handler ollama implementation.
    """

    def __init__(self, agent_name: str = "ui_agent", model_name: str = "gemma3n:e4b", agent_aliases: Optional[str] = "ui", debug: bool = True):
        super().__init__(agent_name, model_name, agent_aliases, debug)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the UI agent asynchronously with streaming support."""
        try:
            self.state.status = "running"
            self.state.started_at = datetime.now()
            
            # Extract user prompt and optional callback for streaming
            user_prompt = input_data.get("prompt", "")
            callback = input_data.get("callback")
            conversation_history = input_data.get("conversation_history", [])
            
            if not user_prompt:
                raise ValueError("No prompt provided in input_data")
            
            # Build context for the UI agent
            context_data = self._build_context(input_data)
            
            # Build the system context using the template
            system_context = self._build_prompt(context_data)
            
            # Call Ollama with streaming support
            response = await self._call_ollama_async(
                prompt=user_prompt,  # User's actual prompt
                context=system_context,  # System context with song/fixture info
                callback=callback,
                conversation_history=conversation_history,
                auto_execute_commands=False  # Disable auto-execution, we handle it in _process_response_actions
            )
            
            # Process any action commands found in the response
            await self._process_response_actions(response)
            
            self.state.status = "completed"
            self.state.completed_at = datetime.now()
            self.state.result = response
            
            return {
                "success": True,
                "response": response,
                "agent": self.agent_name
            }
            
        except Exception as e:
            self.state.status = "error"
            self.state.error = str(e)
            self.state.completed_at = datetime.now()
            
            return {
                "success": False,
                "error": str(e),
                "agent": self.agent_name
            }

    def _build_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the context for the UI agent from the input data."""
        from ...models.app_state import app_state
        
        # Prepare song data
        song = app_state.current_song
        song_data = {}
        
        # Handle case when no song is loaded
        if song is None:
            raise ValueError("No song is currently loaded. Please load a song to build the UI context.")

        # Extract song data for template with safe attribute access
        try:
            song_data = {
                "title": getattr(song, 'song_name', 'Unknown'),
                "bpm": getattr(song, 'bpm', 120),
                "duration": getattr(song, 'duration', 0),
                "arrangement": getattr(song, 'arrangement', []),
                "beats": [],  # Don't send full beats array, agent will request sections as needed
                "key_moments": getattr(song, 'key_moments', [])
            }
        except AttributeError as e:
            # Handle partially initialized song objects
            print(f"⚠️ Warning: Song object missing attributes: {e}")
            song_data = {
                "title": "Unknown Song",
                "bpm": 120,
                "duration": 0,
                "arrangement": [],
                "beats": [],  # Don't send full beats array
                "key_moments": []
            }
        
        # Prepare fixtures data
        fixtures = []
        if app_state.fixtures and hasattr(app_state.fixtures, 'fixtures'):
            fixtures_dict = app_state.fixtures.fixtures
            for fixture_id, fixture in fixtures_dict.items():
                fixtures.append({
                    "id": fixture.id,
                    "type": fixture.fixture_type,
                    "effects": [action for action in fixture.actions if action != 'arm']  # omit 'arm' action
                })
        
        return {
            "song": song_data,
            "fixtures": fixtures
        }

    async def _process_response_actions(self, response: str) -> None:
        """
        Process the AI response to detect and save any action commands, 
        then broadcast the updated actions to the frontend.
        
        Args:
            response (str): The complete AI response text
        """
        try:
            # Extract action commands from the response (lines starting with #action or #)
            action_lines = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith('#action') or (line.startswith('#') and any(word in line for word in ['flash', 'strobe', 'fade', 'seek', 'arm'])):
                    action_lines.append(line)
            
            if not action_lines:
                print("📝 No action commands found in AI response")
                return
            
            print(f"🎭 Found {len(action_lines)} action commands in AI response")
            
            # Import here to avoid circular imports
            from ..direct_commands import DirectCommandsParser
            from ...models.app_state import app_state
            from ..utils.broadcast import broadcast_to_all
            
            # Create direct commands parser
            direct_commands_parser = DirectCommandsParser()
            
            # Process each action command
            actions_added = 0
            for action_line in action_lines:
                try:
                    # Parse and execute the action command
                    success, message, additional_data = await direct_commands_parser.parse_command(action_line)
                    if success:
                        actions_added += 1
                        print(f"✅ Action executed: {action_line}")
                    else:
                        print(f"❌ Action failed: {action_line} -> {message}")
                except Exception as e:
                    print(f"❌ Error processing action '{action_line}': {e}")
            
            # If actions were added successfully, broadcast the updated actions to frontend
            if actions_added > 0 and app_state.current_song_file:
                from pathlib import Path
                from ...models.actions_sheet import ActionsSheet
                
                # Get current actions
                song_name = Path(app_state.current_song_file).stem
                actions_sheet = ActionsSheet(song_name)
                actions_sheet.load_actions()
                
                # Log the actions update
                action_count = len(actions_sheet.actions)
                print(f"📊 Broadcasting actions update: {action_count} total actions for song '{song_name}' (added {actions_added} new)")
                
                # IMPORTANT: Render actions to canvas so they appear on the main canvas
                try:
                    # Automatically render actions to canvas after adding them
                    render_success, render_message, render_data = await direct_commands_parser.parse_command("#render")
                    if render_success:
                        print(f"✅ Actions rendered to canvas: {render_message}")
                    else:
                        print(f"⚠️ Failed to render actions to canvas: {render_message}")
                except Exception as render_error:
                    print(f"❌ Error rendering actions to canvas: {render_error}")
                
                # Broadcast actions update to all clients
                await broadcast_to_all({
                    "type": "actionsUpdate",
                    "actions": [action.to_dict() for action in actions_sheet.actions]
                })

            
        except Exception as e:
            print(f"❌ Error in _process_response_actions: {e}")
