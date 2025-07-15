"""DMX control WebSocket handlers."""

import asyncio
from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..utils.broadcast import broadcast_to_all

# Store pending DMX updates and debounce task
_dmx_pending_updates = {}
_dmx_update_task = None
_dmx_debounce_delay = 0.5  # 500ms

async def handle_set_dmx(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle DMX channel value updates with debouncing."""
    from ...dmx_controller import set_channel
    global _dmx_update_task, _dmx_pending_updates
    
    values = message.get("values", {})
    
    # Update pending changes
    for ch_str, val in values.items():
        try:
            ch = int(ch_str)
            val = int(val)
            if 0 <= ch <= 512 and 0 <= val <= 255:
                _dmx_pending_updates[ch] = val
        except (ValueError, TypeError):
            print(f"❌ Invalid DMX channel or value: {ch_str}={val}")
            continue
    
    # Cancel existing debounce task if any
    if _dmx_update_task:
        _dmx_update_task.cancel()
    
    # Start new debounce task
    _dmx_update_task = asyncio.create_task(_debounced_dmx_update())

async def _debounced_dmx_update() -> None:
    """Execute DMX updates after debounce delay."""
    global _dmx_pending_updates, _dmx_update_task
    try:
        # Wait for debounce delay
        await asyncio.sleep(_dmx_debounce_delay)
        
        # Apply all pending updates
        if _dmx_pending_updates:
            from ...dmx_controller import set_channel, get_universe, send_artnet
            
            updates = {}
            for ch, val in _dmx_pending_updates.items():
                if set_channel(ch, val):
                    updates[ch] = val
            
            # Send ArtNet update
            universe_data = get_universe()
            send_artnet(0, bytes(universe_data))
            
            # Broadcast to all WebSocket clients
            await broadcast_to_all({
                "type": "dmx_update",
                "universe": get_universe()
            })
            
            print(f"🎛️ DMX updated: {len(updates)} channels")
            
            # Clear pending updates
            _dmx_pending_updates.clear()
            
    except asyncio.CancelledError:
        # Task was cancelled, this is expected behavior
        pass
    except Exception as e:
        print(f"❌ Error in debounced DMX update: {e}")
    finally:
        _dmx_update_task = None
