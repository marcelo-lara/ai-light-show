"""DMX control router for playback operations."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..services.dmx.dmx_player import dmx_player

router = APIRouter(prefix="/api/dmx", tags=["DMX Control"])


@router.post("/play")
async def start_playback() -> Dict[str, Any]:
    """Start DMX playback."""
    dmx_player.play()
    return {
        "status": "success",
        "message": "Playback started",
        "is_playing": dmx_player.playback_state.is_playing,
        "current_time": dmx_player.playback_state.get_current_time()
    }


@router.post("/pause")
async def pause_playback() -> Dict[str, Any]:
    """Pause DMX playback."""
    dmx_player.pause()
    return {
        "status": "success", 
        "message": "Playback paused",
        "is_playing": dmx_player.playback_state.is_playing,
        "current_time": dmx_player.playback_state.get_current_time()
    }


@router.post("/stop")
async def stop_playback() -> Dict[str, Any]:
    """Stop DMX playback."""
    dmx_player.stop()
    return {
        "status": "success",
        "message": "Playback stopped", 
        "is_playing": dmx_player.playback_state.is_playing,
        "current_time": dmx_player.playback_state.get_current_time()
    }


@router.post("/seek")
async def seek_playback(time: float) -> Dict[str, Any]:
    """Seek to a specific time position."""
    if time < 0:
        raise HTTPException(status_code=400, detail="Time cannot be negative")
        
    dmx_player.seek(time)
    return {
        "status": "success",
        "message": f"Seeked to {time:.3f}s",
        "is_playing": dmx_player.playback_state.is_playing,
        "current_time": dmx_player.playback_state.get_current_time()
    }


@router.get("/status")
async def get_playback_status() -> Dict[str, Any]:
    """Get current playback status."""
    return {
        "is_playing": dmx_player.playback_state.is_playing,
        "current_time": dmx_player.playback_state.get_current_time(),
        "fps": dmx_player.fps,
        "engine_running": dmx_player.is_running
    }
