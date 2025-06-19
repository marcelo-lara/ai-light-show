from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
from backend.dmx_state import set_channel, get_universe, send_artnet
from fastapi import WebSocket, WebSocketDisconnect

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/dmx/universe")
async def get_dmx_universe():
    return {"universe": get_universe()}

@app.post("/dmx/set")
async def set_dmx_values(request: Request):
    data = await request.json()
    values = data.get("values", {})
    updates = {}
    for ch_str, val in values.items():
        try:
            ch = int(ch_str)
            val = int(val)
            if set_channel(ch, val):
                updates[ch] = val
        except Exception as e:
            return {"error": str(e)}
    send_artnet()
    await broadcast({"type": "dmx_update", "universe": get_universe()})
    return {"updated": updates}

@app.get("/test/artnet")
def test_artnet_send():
    set_channel(15, 255)  # DMX Channel 16 (0-based index)
    set_channel(18, 255)  # DMX Channel 19
    send_artnet()
    return {"sent": True}

clients = []


## WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    print(f"🧠 Client connected: {websocket.client}")
    try:
        while True:
            await websocket.receive_text()  # Placeholder to keep the connection alive
    except WebSocketDisconnect:
        clients.remove(websocket)
        print(f"👋 Client disconnected: {websocket.client}")

async def broadcast(message: dict):
    disconnected = []
    for ws in clients:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    for ws in disconnected:
        clients.remove(ws)

## Static file serving
app.mount("/songs", StaticFiles(directory="static/songs"), name="songs")
app.mount("/fixtures", StaticFiles(directory="static/fixtures"), name="fixtures")
app.mount("/", StaticFiles(directory="static", html=True), name="static")
