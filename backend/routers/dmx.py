"""DMX control router for the AI Light Show system."""

from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException
from ..dmx_controller import set_channel, get_universe, send_artnet, send_canvas_frames
from ..services.dmx_canvas import DmxCanvas
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
        # Create test frame with channels 16 and 19 at full intensity
        frame = [0] * 512
        frame[15] = 255  # Channel 16 (0-based index 15)
        frame[18] = 255  # Channel 19 (0-based index 18)
        send_artnet(0, bytes(frame))
        return {"sent": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-test")
async def start_test_show():
    """Start a test light show pattern"""
    try:
        # Create test canvas with 5 second duration at 30 FPS
        canvas = DmxCanvas(fps=30, duration=5.0)
        
        # Paint test pattern - fade channels 20-40 over 5 seconds
        for channel in range(20, 41):
            canvas.paint_channel(
                channel=channel,
                start_time=0.0,
                duration=5.0,
                value_fn=lambda t: int(t * 255)  # t ranges 0.0-1.0 over duration
            )
            
        send_canvas_frames(canvas)
        return {"status": "show_started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
