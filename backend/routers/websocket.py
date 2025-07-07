"""WebSocket router for real-time communication."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.websocket_service import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Main WebSocket endpoint for real-time communication."""
    await ws_manager.connect(websocket)
    
    try:
        while True:
            message = await websocket.receive_json()
            await ws_manager.handle_message(websocket, message)
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
