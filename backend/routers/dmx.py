"""DMX control router for the AI Light Show system."""

from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from ..dmx_controller import set_channel, get_universe, send_artnet
from ..models.app_state import app_state

router = APIRouter(prefix="/dmx", tags=["dmx"])


@router.get("/universe")
async def get_dmx_universe() -> Dict[str, Any]:
    """Get the current DMX universe state."""
    return {"universe": get_universe()}


@router.post("/set")
async def set_dmx_values(request: Request) -> Dict[str, Any]:
    """Set DMX channel values."""
    try:
        data = await request.json()
        values = data.get("values", {})
        updates = {}
        
        for ch_str, val in values.items():
            try:
                ch = int(ch_str)
                val = int(val)
                if set_channel(ch, val):
                    updates[ch] = val
            except ValueError as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid channel or value: {ch_str}={val}"
                )
        
        send_artnet()
        
        # Broadcast update to all WebSocket clients
        from ..services.websocket_service import broadcast_to_all
        await broadcast_to_all({
            "type": "dmx_update", 
            "universe": get_universe()
        })
        
        return {"updated": updates}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test/artnet")
async def test_artnet_send() -> Dict[str, bool]:
    """Test ArtNet communication by setting specific channels."""
    try:
        set_channel(15, 255)  # DMX Channel 16 (0-based index)
        set_channel(18, 255)  # DMX Channel 19
        send_artnet()
        return {"sent": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
