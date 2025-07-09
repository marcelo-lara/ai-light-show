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
