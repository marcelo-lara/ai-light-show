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

    def __init__(self, agent_name: str = "ui_agent", model_name: str = "cgemma3n:e4b", agent_aliases: Optional[str] = "ui"):
        super().__init__(agent_name, model_name, agent_aliases)

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the UI agent asynchronously with streaming support."""
        try:
            self.state.status = "running"
            self.state.started_at = datetime.now()
            
            # Extract user prompt and optional callback for streaming
            user_prompt = input_data.get("prompt", "")
            callback = input_data.get("callback")
            websocket = input_data.get("websocket")
            conversation_history = input_data.get("conversation_history", [])
            
            if not user_prompt:
                raise ValueError("No prompt provided in input_data")
            
            # Build context for the UI agent
            context = self._build_context(input_data)
            
            # Build the complete prompt using the template
            prompt_with_context = self._build_prompt(context)
            
            # Call Ollama with streaming support
            response = await self._call_ollama_async(
                prompt=user_prompt,
                context=prompt_with_context,
                callback=callback,
                websocket=websocket,
                conversation_history=conversation_history,
                auto_execute_commands=True  # Enable auto-execution of action commands
            )
            
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
                "beats": song.get_beats_array() if hasattr(song, 'get_beats_array') and callable(getattr(song, 'get_beats_array', None)) else [],
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
                "beats": [],
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
