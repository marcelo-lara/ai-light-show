"""Utilities for WebSocket broadcasting."""

from typing import Dict, Any
from ...models.app_state import app_state

async def broadcast_to_all(message: Dict[str, Any]) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    disconnected = []
    for ws in app_state.websocket_clients:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        app_state.remove_client(ws)
