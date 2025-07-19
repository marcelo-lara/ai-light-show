"""
Lighting Pipeline WebSocket Handler
"""
from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..langgraph.lighting_pipeline import run_lighting_pipeline
from ..utils.broadcast import broadcast_to_all

async def handle_run_lighting_pipeline(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """
    Handle 'runLightingPipeline' WebSocket message to trigger the lighting pipeline.
    """
    try:
        # Optionally, accept segment input from message
        segment_input = message.get('segment')
        if not segment_input:
            # Use current song segment if available
            if not app_state.current_song:
                await websocket.send_json({
                    "type": "pipelineResult",
                    "status": "error",
                    "message": "No song is currently loaded."
                })
                return
            # Use the current song's segment info
            segment_input = {
                "segment": {
                    "name": getattr(app_state.current_song, 'title', 'Unknown'),
                    "start": 0.0,
                    "end": getattr(app_state.current_song, 'duration', 0.0),
                    "features": getattr(app_state.current_song, 'features', {})
                }
            }
        # Run the pipeline
        result = run_lighting_pipeline(segment_input)
        await websocket.send_json({
            "type": "pipelineResult",
            "status": "ok",
            "result": result
        })
        # Optionally broadcast DMX update if result contains DMX commands
        if result and result.get("dmx"):
            await broadcast_to_all({
                "type": "dmxCanvasUpdated",
                "universe": result["dmx"],
                "message": "DMX Canvas updated by lighting pipeline"
            })
    except Exception as e:
        await websocket.send_json({
            "type": "pipelineResult",
            "status": "error",
            "message": str(e)
        })
