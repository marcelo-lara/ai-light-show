# AI Light Show Designer

This project is a full-stack system for designing and playing synchronized DMX light shows to music. It includes:

* 🎛️ **Fixture Controls** (Preact frontend)
* 🎵 **Cue-based song syncing**
* 🕹️ **Real-time Art-Net packet sending**
* 🧠 **Pre-rendered DMX timelines for playback accuracy**

---

## 🧩 System Components

### Frontend (Preact + Vite)

* Visual editor for fixtures, cues, and arrangement
* Loads fixtures from `/static/fixtures/master_fixture_config.json`
* Loads presets from `/static/fixture_presets.json`
* Cues are visualized and controlled inside the "Song Cue Controls" card
* Sends DMX updates and cue events via fetch and WebSocket

### Backend (FastAPI)

* Static file server for frontend
* Art-Net UDP packet sender (40Hz loop)
* DMX state tracking (512-channel universe)
* Pre-renders cue timeline based on song and fixtures
* Receives playback time sync over WebSocket (`/ws/player`)

---

## 🔌 Fixture Model

Defined in `master_fixture_config.json`:

```json
{
  "parcan_left": {
    "type": "rgb",
    "start_channel": 16,
    "channels": ["dim", "red", "green", "blue", "strobe"],
    "arm": { "dim": 255 }
  },
  "head_mh": {
    "type": "moving_head",
    "start_channel": 1,
    "channels": ["pan", "pan_fine", "tilt", "tilt_fine", "shutter", "color"],
    "arm": { "shutter": 255 },
    "channel_ranges": {
      "color": {
        "0": "white",
        "24": "yellow"
      }
    }
  }
}
```

---

## 🎨 Fixture Presets

Stored in `fixture_presets.json`. Example:

```json
{
  "name": "fade-to-blue",
  "type": "rgb",
  "mode": "single",
  "parameters": { "duration": 1000 },
  "steps": [
    { "type": "fade", "to": { "blue": 255 }, "duration": 1000 }
  ]
}
```

* Applied per fixture
* Steps support `fade` and `set`
* Evaluated and rendered into timeline on backend

---

## 🎬 Song Cues

Stored in `public/songs/songname.mp3.cues.json`

```json
[
  {
    "fixture_id": "parcan_left",
    "preset": "fade-to-blue",
    "start_time": 0.0,
    "parameters": { "duration": 4000 }
  }
]
```

---

## 🕒 Timeline Rendering

* `main.py` loads cues and presets at startup
* Renders all cue events into a `timeline` list
* Timeline is looped and executed in sync with current song time

---

## 🎙️ Playback Sync

* Audio is played on frontend
* WebSocket `/ws/player` syncs:

  ```json
  { "isPlaying": true, "currentTime": 12.4 }
  ```
* Backend uses this to track and drive timeline execution

---

## 🚀 Running the Project

1. Build & start with Docker:

   ```sh
   docker compose up --build
   ```
2. Visit [http://localhost:5000](http://localhost:5000)
3. Upload a song, edit fixtures, trigger presets, and watch your lights sync

---

## 📂 Directory Structure

```
frontend/
  ├─ app.jsx
  └─ FixtureCard.jsx
backend/
  ├─ main.py
  ├─ dmx_state.py
static/
  ├─ songs/
  ├─ fixtures/master_fixture_config.json
  ├─ fixture_presets.json
```

---

## ✅ TODO / Next Steps

* [ ] Group/chaser animation system
* [ ] Fixture preview rendering
* [ ] Timeline editor UI
* [ ] Offline export (cue to binary DMX)

---

## License

MIT (c) 2025


------------------------------------------------------
🧠 AI Light Show Project – Base Context for GPT-4o
Goal:
Develop a full-stack system (Preact frontend + Python FastAPI backend) to design and play synchronized DMX light shows based on music timeline and fixture presets.

🎛️ DMX Fixtures
Fixtures defined in /static/fixtures/master_fixture_config.json

Each fixture has channels (e.g., dimmer, red, green, blue), starting DMX address, and type (e.g., rgb, moving_head)

Fixtures may require an "ARM" state:

rgb: dim must be 255 to see colors

moving_head: shutter must be 255 to output light

Some channels represent discrete options (e.g., Gobos or Color wheels using defined value ranges)

🎬 Fixture Presets
Loaded from /static/fixture_presets.json

Preset contains:

type: fixture type it applies to (rgb, etc.)

mode: "single" or "loop"

parameters: e.g., duration, intensity

steps: array of actions

set: directly assign values to channels

fade: interpolate to new values over time

Only applies to one fixture at a time

🎵 Song Cues
Each song has a cue list: songname.mp3.cues.json

Cue structure includes:

fixture_id

preset_name

start_time (in seconds)

parameters overrides (e.g., duration)

Cue lists are stored, loaded, and visualized independently from the song arrangement

⏱️ Timeline & Playback
Cues are pre-rendered server-side into a timeline variable for real-time playback

Backend sends Art-Net UDP packets continuously at ~40Hz based on timeline and current_playback_time

Frontend syncs isPlaying and currentTime to backend via WebSocket (/ws/player)

Precise timecode and low-latency packet delivery is critical

📦 Backend (FastAPI)
Serves static frontend files (Vite/Preact build)

Exposes:

/dmx/set: sets DMX channel values

/dmx/universe: dumps current DMX state

/songs/save: saves arrangement or cues

/ws/player: syncs frontend playback

Internal: dmx_state.py handles Art-Net UDP sending and DMX buffer logic

💻 Frontend (Preact)
UI shows:

Audio waveform + transport controls

Arrangement markers (e.g., intro, drop)

Fixtures panel (DMX sliders, presets)

Cue controls (add, edit, trigger)

Sends cue triggers, DMX updates, and playback time to backend

Uses WebSockets for state sync and fetch API for updates
