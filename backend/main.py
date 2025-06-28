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
from backend.timeline_engine import render_timeline, execute_timeline
from backend.chaser_utils import expand_chaser_template, get_chasers
from backend.song_utils import get_songs_list, load_song_metadata, save_song_metadata
from backend.fixture_utils import load_fixtures_config
from backend.song_metadata import SongMetadata, Section
from backend.song_analyze import song_analyze
from backend.ai.essentia_analysis import extract_with_essentia
from backend.ai.essentia_chords import extract_chords_and_align
from backend.config import SONGS_DIR
from fastapi import WebSocket, WebSocketDisconnect

# ArtNet Fixture Config and Presets
fixture_config = []
fixture_presets = []
current_song = None

# Cue management
cue_list = []
current_song_file = None
song_metadata = {}
song = None

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

def load_cues(song_file):
    global cue_list
    cue_path = SONGS_DIR / f"{song_file}.cues.json"

    if not cue_path.exists():
        print(f"⚠️ No cues found for {song_file}, creating empty cue list.")
        cue_list.clear()
        return

    try:
        with open(cue_path) as f:
            cue_list.clear()
            cue_list.extend(json.load(f))
        print(f"🎵 Loaded cues for {song_file} ({len(cue_list)} total)")
    except Exception as e:
        print(f"❌ load_cues error: {e}")

def save_cues(song_file, cues):
    cue_path = SONGS_DIR / f"{song_file}.cues.json"
    try:
        cue_path.write_text(json.dumps(cues, indent=2))
        print(f"💾 Saved cues to {cue_path}")
    except Exception as e:
        print(f"❌ save_cues error: {e}")
    bpm = song_metadata.get("bpm", 100)
    render_timeline(fixture_config, fixture_presets, cues=cues, current_song=song_file, bpm=bpm)        


# 🎵 WebSocket for playback state synchronization 
timeline = []
playback_time = 0.0
start_monotonic = 0.0
last_sent = 0.0
is_playing = False

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global is_playing, playback_time, start_monotonic, current_song_file, cue_list, song

    await websocket.accept()
    clients.append(websocket)
    print(f"🧠 Client connected: {websocket.client}")
    await websocket.send_json({
        "type": "setup",
        "songs": get_songs_list(),
        "fixtures": fixture_config,
        "presets": fixture_presets,
        "chasers": get_chasers()
    })
    try:
        while True:
            msg = await websocket.receive_json()

            if msg.get("type") == "sync":
                if "isPlaying" in msg:
                    is_playing = msg["isPlaying"]
                if "currentTime" in msg:
                    playback_time = msg["currentTime"]
                    if is_playing:
                        start_monotonic = time.monotonic() - playback_time

                await websocket.send_json({
                    "type": "syncAck",
                    "isPlaying": is_playing,
                    "currentTime": playback_time
                })
                # print(f"[WS] Sync: isPlaying={is_playing}, currentTime={playback_time}")

            elif msg.get("type") == "loadSong":
                print(f"🎶 Loading song: {msg['file']}")
                current_song_file = msg["file"]
                
                song = SongMetadata(current_song_file, songs_folder=SONGS_DIR)
                load_cues(current_song_file)

                await websocket.send_json({
                    "type": "songLoaded",
                    "metadata": song.to_dict(),
                    "cues": cue_list,                    
                })
                bpm = song.bpm
                render_timeline(fixture_config, fixture_presets, cues=cue_list, current_song=current_song_file, bpm=bpm)


            elif msg.get("type") == "getCues":
                print(f"🔍 Fetching cues for {current_song_file}")
                await websocket.send_json({
                    "type": "cuesUpdated",
                    "cues": cue_list
                })

            elif msg.get("type") == "addCue":
                cue = msg["cue"]

                if 'duration' not in cue:
                    if 'parameters' in cue and 'loop_duration' in cue['parameters']:
                        cue['duration'] = cue['parameters']['loop_duration']
                    else:
                        cue['duration'] = cue['parameters']['fade_duration'] if 'fade_duration' in cue['parameters'] else 0

                cue_list.append(cue)
                cue_list.sort(key=lambda c: (c["fixture"], c["time"]))  # Sort by fixture and time
                print(f"📝 Added new cue: {cue}")
           
                save_cues(current_song_file, cue_list)
                
                await websocket.send_json({
                    "type": "cuesUpdated",
                    "cues": cue_list
                })

            elif msg.get("type") == "updateCues":
                cues = msg["cues"]
                cue_list.clear()
                cues.sort(key=lambda c: (c["time"], c["fixture"]))  # Sort by time and fixture
                cue_list.extend(cues)
                print(f"📝 Updated cues: {len(cues)} cues")
                save_cues(current_song_file, cue_list)
                await websocket.send_json({
                    "type": "cuesUpdated",
                    "cues": cue_list
                })

            elif msg.get("type") == "updateCue":
                updated = msg["cue"]
                for i, c in enumerate(cue_list):
                    if c["fixture"] == updated["fixture"] and c["time"] == updated["time"]:
                        cue_list[i] = updated
                        print(f"📝 Updated cue: {updated}")
                        break

                save_cues(current_song_file, cue_list)
                await websocket.send_json({
                    "type": "cuesUpdated",
                    "cues": cue_list
                })

            elif msg.get("type") == "deleteCue":
                cue = msg["cue"]

                if "chaser_id" in cue:
                    cid = cue["chaser_id"]
                    cue_list[:] = [c for c in cue_list if c.get("chaser_id") != cid]
                    print(f"🗑️ Deleted chaser group '{cid}'")
                else:
                    cue_list[:] = [c for c in cue_list if not (
                        c["fixture"] == cue["fixture"] and c["time"] == cue["time"]
                    )]

                save_cues(current_song_file, cue_list)
                await websocket.send_json({
                    "type": "cuesUpdated",
                    "cues": cue_list
                })

            elif msg.get("type") == "saveArrangement":
                arrangement = msg["arrangement"]
                if song is not None:
                    song.arrangement = {k: Section(**v) for k, v in arrangement.items()}
                    song.save()
                else:
                    print("No song object loaded; cannot save arrangement.")

            elif msg.get("type") == "insertChaser":
                chaser_name = msg["chaser"]
                insert_time = msg["time"]
                user_params = msg.get("parameters", {})
                chaser_id = msg.get("chaser_id")

                bpm = song_metadata.get("bpm", 120)
                new_cues = expand_chaser_template(chaser_name, insert_time, bpm)

                for cue in new_cues:
                    cue["parameters"].update(user_params)
                    cue["chaser"] = chaser_name
                    cue["chaser_id"] = chaser_id

                cue_list.extend(new_cues)
                cue_list.sort(key=lambda c: (c["time"], c["fixture"]))
                save_cues(current_song_file, cue_list)

                await websocket.send_json({
                    "type": "cuesUpdated",
                    "cues": cue_list
                })

            elif msg.get("type") == "analyzeSong":
                if not song:
                    print("❌ No song loaded for analysis")
                    return
                print(f"🔍 Analyzing song: {song.title} ({song.mp3_path})")

                song = song_analyze(song)
                song.save()

                await websocket.send_json({
                    "type": "analyzeResult",
                    "status": "ok",
                    "songMetadata": song.to_dict()
                })

            else:
                print(f"❓ Unknown message type: {msg.get('type')}")
                await websocket.send_json({"type": "error", "message": "Unknown message type"})

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
app.mount("/", StaticFiles(directory="static", html=True), name="static")

## Test function to generate beat sync cues ------------------------------------
def test_beat_sync(song_beats):
    fixtures_id = ["parcan_pl", "parcan_pr", "parcan_l", "parcan_r"]
    cue_template = {
        "time": 0,
        "fixture": "parcan_l",
        "preset": "flash",
        "parameters": {
            "fade_beats": 1
        },
        "duration": 1,
        "chaser": "ai",
        "chaser_id": "ai_generated_000"
    }
    
    # create flash cues for each beat
    cue_list.clear()
    curr_fixture_idx = 0
    for beat in song_beats:
        # cycle through fixtures
        fixture = fixtures_id[curr_fixture_idx]
        cue = cue_template.copy()
        cue["time"] = beat
        cue["fixture"] = fixture
        cue_list.append(cue)
        curr_fixture_idx += 1
        if curr_fixture_idx >= len(fixtures_id):
            curr_fixture_idx = 0

    render_timeline(fixture_config, fixture_presets, cues=cue_list, current_song=current_song, bpm=song_metadata['bpm'])
    return cue_list    

# -----------------------------------------------------------------------------
# Timeline executor to run the timeline engine
# -----------------------------------------------------------------------------
async def timeline_executor():
    global last_sent, is_playing, playback_time, fixture_config, fixture_presets, start_monotonic
    fixture_config, fixture_presets = load_fixtures_config()

    while True:
        if is_playing:
            now = time.monotonic() - start_monotonic
            execute_timeline(now)
        await asyncio.sleep(0.01)
