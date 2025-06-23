import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import json
from backend.dmx_controller import set_channel, get_universe, send_artnet
from backend.timeline_engine import render_timeline, load_song_cues, execute_timeline
from fastapi import WebSocket, WebSocketDisconnect

SONGS_DIR = Path("/app/static/songs")

# ArtNet Fixture Config and Presets
fixture_config = []
fixture_presets = []
current_song = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(timeline_executor())
    yield

app = FastAPI(lifespan=lifespan)

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

@app.post("/songs/save")
async def save_song_data(request: Request):
    payload = await request.json()
    file = payload.get("fileName")
    data = payload.get("data")

    if not file or not data:
        print("ERROR: Missing file or data in request payload")
        print(f"    fileName: {file}")
        print(f"    data: {data}")
        return {"status": "error", "message": "Missing file or data"}

    file_path = SONGS_DIR / file
    try:
        file_path.write_text(json.dumps(data, indent=2))
        return {"status": "ok", "message": f"{file} saved."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/test/artnet")
def test_artnet_send():
    set_channel(15, 255)  # DMX Channel 16 (0-based index)
    set_channel(18, 255)  # DMX Channel 19
    send_artnet()
    return {"sent": True}

clients = []

# Global variables to hold fixture config and presets

@app.post("/renderSong")
async def render_song(request: Request):
    global timeline, fixture_config, fixture_presets, current_song
    payload = await request.json()
    current_song = payload.get("fileName")
    if not current_song:
        return {"error": "Missing 'file' in request"}

    render_timeline(fixture_config, fixture_presets, current_song=current_song, fps=120)

    return {"status": "ok", "fixture_count": len(fixture_config)}

def load_fixtures_config():
    global fixture_config, fixture_presets
    try:
        with open("/app/static/fixtures/master_fixture_config.json") as f:
            fixture_config = json.load(f)
        with open("/app/static/fixtures/fixture_presets.json") as f:
            fixture_presets = json.load(f)
        print(f"✅ Loaded fixture config with {len(fixture_config)} fixtures and {len(fixture_presets)} presets.")            
    except Exception as e:
        print("❌ load_fixtures_config error: ", e)

# 🎵 WebSocket for playback state synchronization 
timeline = []
playback_time = 0.0
start_monotonic = 0.0
last_sent = 0.0
is_playing = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global is_playing, playback_time, start_monotonic

    await websocket.accept()
    clients.append(websocket)
    print(f"🧠 Client connected: {websocket.client}")
    try:
        while True:
            # await websocket.receive_text()  # Placeholder to keep the connection alive
            msg = await websocket.receive_json()
            if "isPlaying" in msg:
                is_playing = msg["isPlaying"]
            if "currentTime" in msg:
                playback_time = msg["currentTime"]
                if is_playing:
                    start_monotonic = time.monotonic() - playback_time

            await websocket.send_json({
                "status": "ok",
                "isPlaying": is_playing,
                "currentTime": playback_time
            })
            
            print(f"[WS] Sync: isPlaying={is_playing}, currentTime={playback_time}")


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

async def timeline_executor():
    global last_sent, is_playing, playback_time
    print("🌀 Timeline executor started")
    load_fixtures_config()

    while True:
        if is_playing:
            now = time.monotonic() - start_monotonic
            execute_timeline(now)
        await asyncio.sleep(0.01)
