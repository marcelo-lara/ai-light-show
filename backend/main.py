from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os, json
import asyncio, time
import socket


# --- Constants and App Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(timeline_executor())
    yield
    
app = FastAPI(lifespan=lifespan)
SONGS_DIR = "/app/static/songs"
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../static"))

# --- CORS (if frontend makes API calls from another origin) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Frontend ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# --- DMX State ---
dmx_universe = [0] * 512
active_connections = set()

@app.get("/dmx/universe")
async def get_universe():
    return {"universe": dmx_universe}

@app.post("/dmx/set")
async def set_dmx_values(request: Request):
    data = await request.json()
    values = data.get("values", {})
    updates = {}
    for ch_str, val in values.items():
        try:
            ch = int(ch_str)
            val = int(val)
            if 0 <= ch < 512 and 0 <= val <= 255:
                dmx_universe[ch] = val
                updates[ch] = val
        except Exception as e:
            return {"error": str(e)}
    send_artnet(dmx_universe)    
    await broadcast({"type": "dmx_update", "universe": dmx_universe})
    return {"updated": updates}

# --- Song Arrangement Save ---
@app.post("/songs/save")
async def save_arrangement(request: Request):
    data = await request.json()
    file = data.get("file")
    if not file:
        return {"error": "Missing file name"}
    filepath = os.path.join(SONGS_DIR, file)
    try:
        with open(filepath, "w") as f:
            json.dump(data["data"], f, indent=2)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- WebSocket API ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast(message: dict):
    for ws in active_connections.copy():
        try:
            await ws.send_json(message)
        except:
            active_connections.remove(ws)

# --- ArtNet -----------------------

ARTNET_PORT = 6454
ARTNET_IP = "255.255.255.255"  # or set to a specific node IP if needed
ARTNET_UNIVERSE = 0  # usually 0 unless you're using multiple universes

def build_artnet_packet(data):
    # Art-Net header
    packet = bytearray()
    packet.extend(b'Art-Net\x00')          # ID
    packet.extend((0x00, 0x50))            # OpCode ArtDMX
    packet.extend((0x00, 0x0e))            # Protocol version
    packet.extend((0x00, 0x00))            # Sequence + Physical
    packet.extend((ARTNET_UNIVERSE & 0xFF, (ARTNET_UNIVERSE >> 8) & 0xFF))  # Universe low/high
    packet.extend((0x02, 0x00))            # Length high/low (512 bytes)
    packet.extend(bytes(data[:512]))       # DMX data
    return packet

def send_artnet(data):
    packet = build_artnet_packet(data)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(packet, (ARTNET_IP, ARTNET_PORT))
    sock.close()

# --- ArtNet Playback ---
timeline = []           # Sorted by time
start_time = time.monotonic()  # Reference point

async def timeline_executor():
    global dmx_universe, timeline
    last_sent = 0
    while True:
        now = time.monotonic() - start_time
        for cue in timeline:
            if last_sent < cue["time"] <= now:
                for ch, val in cue["values"].items():
                    dmx_universe[ch] = val
                send_artnet(dmx_universe)
                await broadcast({"type": "dmx_update", "universe": dmx_universe})
        last_sent = now
        await asyncio.sleep(0.01)  # ~100 FPS update rate

