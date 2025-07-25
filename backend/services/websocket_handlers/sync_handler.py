"""Sync and playback WebSocket handlers."""

from typing import Dict, Any
from fastapi import WebSocket

async def handle_sync(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle playback synchronization."""
    from ..dmx.dmx_player import dmx_player
    
    # Frontend has complete control over playback state - no fallbacks
    is_playing = message.get("isPlaying", False)  # Default to stopped if not specified
    current_time = message.get("currentTime", 0.0)  # Default to beginning if not specified
    
    dmx_player.sync_playback(is_playing, current_time)

    await websocket.send_json({
        "type": "syncAck",
        "isPlaying": dmx_player.playback_state.is_playing,
        "currentTime": dmx_player.playback_state.get_current_time()
    })

async def handle_blackout(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle blackout request."""
    from ...dmx_controller import send_blackout
    send_blackout()
