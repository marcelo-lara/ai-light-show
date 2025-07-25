"""WebSocket service for real-time communication."""

from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from ..models.app_state import app_state
from .websocket_handlers import (
    handle_sync,
    handle_blackout,
    handle_load_song,
    handle_save_arrangement,
    handle_save_key_moments,
    handle_save_light_plan,
    handle_analyze_song,
    handle_set_dmx,
    handle_user_prompt,
)
from .utils.broadcast import broadcast_to_all
from pathlib import Path

class WebSocketManager:
    """Manages WebSocket connections and message handling."""
    
    def __init__(self):
        self.message_handlers = {
            "sync": handle_sync,
            "loadSong": handle_load_song,
            "saveArrangement": handle_save_arrangement,
            "saveKeyMoments": handle_save_key_moments,
            "saveLightPlan": handle_save_light_plan,
            "analyzeSong": handle_analyze_song,
            "setDmx": handle_set_dmx,
            "userPrompt": handle_user_prompt,
            "blackout": handle_blackout,
        }

    def _get_llm_status(self) -> str:
        """Get the current LLM status."""
        try:
            from .ollama.ollama_streaming import llm_status
            return llm_status or ""
        except ImportError:
            return ""

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        app_state.add_client(websocket)
        print(f"🧠 Client connected: {websocket.client}")
        
        # Send initial setup data
        # Get actions for current song, if loaded
        actions = []
        if app_state.current_song_file:
            try:
                from ..models.actions_sheet import ActionsSheet
                actions_sheet = ActionsSheet(Path(app_state.current_song_file).stem)
                actions_sheet.load_actions()
                actions = [action.to_dict() for action in actions_sheet.actions]
            except Exception as e:
                print(f"❌ Error loading actions for setup: {e}")
        
        await websocket.send_json({
            "type": "setup",
            "songs": app_state.get_songs_list(),
            "fixtures": app_state.fixture_config,
            "actions": actions,  # Send current actionsheet
            "llm_status": self._get_llm_status(),  # Send current LLM status
        })
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection."""
        app_state.remove_client(websocket)
        
        # Clean up pending actions for this websocket
        from .websocket_handlers.ai_handler import _pending_actions_store
        
        session_id = str(id(websocket))
        if session_id in _pending_actions_store:
            del _pending_actions_store[session_id]
        
        print(f"👋 Client disconnected: {websocket.client}")
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Route message to appropriate handler."""
        msg_type = message.get("type")
        
        if msg_type in self.message_handlers:
            try:
                await self.message_handlers[msg_type](websocket, message)
            except Exception as e:
                print(f"❌ Error handling {msg_type}: {e}")
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Error handling {msg_type}: {str(e)}"
                })
        else:
            print(f"❓ Unknown message type: {msg_type}")
            print(f"  Message content: {message}")            
            await websocket.send_json({
                "type": "error", 
                "message": "Unknown message type"
            })

# Global WebSocket manager instance
ws_manager = WebSocketManager()
