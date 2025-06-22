import asyncio
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import json
from backend.dmx_state import set_channel, get_universe, send_artnet, dmx_universe
from fastapi import WebSocket, WebSocketDisconnect

SONGS_DIR = Path("/app/static/songs")

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


## WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
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

# 🎵 WebSocket for playback state synchronization
timeline = []
playback_time = 0.0
start_monotonic = 0.0
last_sent = 0.0
is_playing = False

@app.websocket("/ws/player")
async def player_socket(websocket: WebSocket):
    global is_playing, playback_time, start_monotonic
    await websocket.accept()
    try:
        while True:
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
    except Exception as e:
        print("WebSocket closed:", e)
        await websocket.close()

## Static file serving
app.mount("/songs", StaticFiles(directory="static/songs"), name="songs")
app.mount("/fixtures", StaticFiles(directory="static/fixtures"), name="fixtures")
app.mount("/", StaticFiles(directory="static", html=True), name="static")

async def timeline_executor():
    global last_sent
    print("🌀 Timeline executor started")
    while True:
        if is_playing:
            now = time.monotonic() - start_monotonic
            for cue in timeline:
                if last_sent < cue["time"] <= now:
                    for ch, val in cue["values"].items():
                        dmx_universe[ch] = val
                    send_artnet()
            last_sent = now
        await asyncio.sleep(0.01)

def render_timeline(cues, fixture_config, fixture_presets):
    timeline = []

    def find_fixture(fid):
        for f in fixture_config:
            if f["id"] == fid:
                return f
        return None

    def find_preset(pname, ftype):
        for p in fixture_presets:
            if p["name"] == pname and p["type"] == ftype:
                return p
        return None

    def interpolate_steps(start_values, end_values, duration, fps=20):
        steps = []
        interval = 1.0 / fps
        total_steps = int(duration / interval)
        for i in range(1, total_steps + 1):
            t = i / total_steps
            step_vals = {
                ch: int(start_values[ch] + t * (end_values[ch] - start_values[ch]))
                for ch in start_values
            }
            steps.append((round(i * interval, 4), step_vals))
        return steps

    for cue in cues:
        start_time = cue["start_time"]
        fixture = find_fixture(cue["fixture_id"])
        if not fixture:
            continue

        preset = find_preset(cue["preset_name"], fixture["type"])
        if not preset:
            continue

        ch_map = fixture["channels"]
        overrides = cue.get("parameters", {})
        loop = preset.get("mode") == "loop"
        loop_duration = overrides.get("loop_duration", 1000) / 1000.0  # ms → sec

        step_offset = 0
        while True:
            for step in preset["steps"]:
                t = start_time + step_offset
                if step["type"] == "set":
                    values = {
                        ch_map[k]: v for k, v in step["values"].items() if k in ch_map
                    }
                    timeline.append({"time": round(t, 4), "values": values})
                elif step["type"] == "fade":
                    duration = overrides.get("duration", step["duration"]) / 1000.0
                    to_vals = {
                        ch_map[k]: v for k, v in step["values"].items() if k in ch_map
                    }
                    from_vals = {ch: 0 for ch in to_vals}
                    fade_steps = interpolate_steps(from_vals, to_vals, duration)
                    for offset, fade_vals in fade_steps:
                        timeline.append({
                            "time": round(t + offset, 4),
                            "values": fade_vals
                        })
                    step_offset += duration
            if loop:
                step_offset += loop_duration
                if step_offset > loop_duration:
                    break
            else:
                break

    return sorted(timeline, key=lambda ev: ev["time"])
