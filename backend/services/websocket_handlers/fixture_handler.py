"""Fixture configuration WebSocket handlers."""

from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ...fixture_utils import load_fixtures_config
from ..utils.broadcast import broadcast_to_all

async def handle_reload_fixtures(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle fixture configuration reload."""
    print("--🔄 Reloading fixture configuration")
    
    # TODO: Update load_fixtures_config to return proper tuple or handle None
    result = load_fixtures_config(force_reload=True)
    if result is not None:
        fixture_config, fixture_presets = result
        app_state.fixture_config = fixture_config
        app_state.fixture_presets = fixture_presets
        
        # Invalidate cached services since fixtures changed
        app_state.invalidate_service_cache()
        
        await broadcast_to_all({
            "type": "fixturesUpdated",
            "fixtures": fixture_config,
            "presets": fixture_presets
        })
    else:
        print("❌ Failed to load fixture configuration")
        await websocket.send_json({
            "type": "error",
            "message": "Failed to reload fixture configuration"
        })
