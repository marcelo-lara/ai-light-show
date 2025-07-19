"""
Agent Stage WebSocket Handler
"""
from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..langgraph.lighting_pipeline import PipelineState
from ..agents import (
    ContextBuilderAgent,
    LightingPlannerAgent,
    EffectTranslatorAgent,
)
from ..utils.broadcast import broadcast_to_all

async def handle_run_agent(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """
    Handle 'runAgent' WebSocket message to run a single agent stage.
    """
    try:
        stage = message.get('stage')
        if not stage:
            await websocket.send_json({
                "type": "agentResult",
                "status": "error",
                "message": "No agent stage specified."
            })
            return
        # Prepare initial state
        if not app_state.current_song:
            await websocket.send_json({
                "type": "agentResult",
                "status": "error",
                "message": "No song is currently loaded."
            })
            return
        segment = {
            "name": getattr(app_state.current_song, 'title', 'Unknown'),
            "start": 0.0,
            "end": getattr(app_state.current_song, 'duration', 0.0),
            "features": getattr(app_state.current_song, 'features', {})
        }
        state: PipelineState = {
            "segment": segment,
            "context_summary": "",
            "actions": [],
            "dmx": []
        }
        # Run the requested agent
        if stage == "context_builder":
            agent = ContextBuilderAgent()
            result = agent.run(state)
        elif stage == "lighting_planner":
            agent = LightingPlannerAgent()
            # Optionally run context builder first
            state = ContextBuilderAgent().run(state)
            result = agent.run(state)
        elif stage == "effect_translator":
            agent = EffectTranslatorAgent()
            # Optionally run context builder and planner first
            state = ContextBuilderAgent().run(state)
            state = LightingPlannerAgent().run(state)
            result = agent.run(state)
        else:
            await websocket.send_json({
                "type": "agentResult",
                "status": "error",
                "message": f"Unknown agent stage: {stage}"
            })
            return
        await websocket.send_json({
            "type": "agentResult",
            "status": "ok",
            "stage": stage,
            "result": result
        })
        # Optionally broadcast DMX update if effect_translator
        if stage == "effect_translator" and result and result.get("dmx"):
            await broadcast_to_all({
                "type": "dmxCanvasUpdated",
                "universe": result["dmx"],
                "message": "DMX Canvas updated by Effect Translator agent"
            })
    except Exception as e:
        await websocket.send_json({
            "type": "agentResult",
            "status": "error",
            "message": str(e)
        })
