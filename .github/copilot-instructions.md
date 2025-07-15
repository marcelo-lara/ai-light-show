# AI Light Show - Development Instructions for AI Coding Agents

## 🎯 Project Overview
AI-driven DMX lighting control system that analyzes music and creates synchronized light shows. Built with Python FastAPI backend and Preact/Vite frontend.

## 🧠 Core Architecture - Essential Mental Model

### Central State Management Pattern
**CRITICAL**: Always use the global `app_state` singleton - never create new instances of core components:
```python
from backend.models.app_state import app_state
# Use existing instances: app_state.dmx_canvas, app_state.fixtures
```

### The Actions-Based Flow
1. **Actions Sheet** (`ActionModel`) - Commands like "flash parcan_l blue at 5.2s"
2. **Actions Service** - Renders actions to DMX Canvas
3. **DMX Canvas** - 512-channel DMX universe storage
4. **Fixtures** - Object-oriented fixture controllers that paint to canvas
5. **DMX Player** - Real-time playback engine with Art-Net output

### Data Flow Architecture
```
Song Analysis → AI Assistant → Actions Sheet → Actions Service → DMX Canvas → DMX Player → Art-Net
```

## 🚫 DEPRECATED SYSTEMS - Do Not Use
All timeline/cue system code, components, and references have been removed. Do not add or use any timeline/cue-related features, files, or comments.

## 🔧 Development Workflows

### Backend Development
```bash
# Setup
cd backend && pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Key entry points
backend/app.py              # FastAPI app with lifespan DMX player management
backend/models/app_state.py # Global singleton state - NEVER recreate
backend/services/websocket_service.py # Real-time frontend communication
```

### Frontend Development
```bash
# Setup  
cd frontend && npm install && npm run dev
# Uses Preact (React-like), TailwindCSS, WaveSurfer.js for audio, WebSocket for real-time sync
```

### Docker Development
```bash
docker-compose up -d  # Full stack with Ollama LLM support
# Access: http://localhost:5500
```

## 🎛️ Key Integration Patterns

### WebSocket Communication Protocol
Frontend ↔ Backend real-time sync:
```javascript
// Frontend patterns
wsSend("loadSong", { file: songFile });
wsSend("setDmx", { values: {10: 255, 11: 128} });
wsSend("userPrompt", { text: "flash red lights" });

// Backend handlers in websocket_service.py
case "loadSong": loads song + analysis
case "setDmx": immediate DMX override
case "userPrompt": AI chat → action proposals
```

### Fixture Action Rendering
```python
# Create actions
action = ActionModel(
    fixture_id="parcan_l", 
    action="flash",
    start_time=5.2,
    parameters={"colors": ["blue"], "duration": 1.5}
)

# Render to canvas
actions_service = ActionsService(app_state.fixtures, app_state.dmx_canvas)
actions_service.render_actions_to_canvas(actions_sheet)
```

### Song Analysis Integration
```python
# Audio analysis with Essentia
song = SongMetadata(song_name="track.mp3", songs_folder=SONGS_DIR)
analyzed = song_analyze(song, reset_file=True)
# Creates: beats, chords, patterns, arrangement sections
```

## 🎵 Project-Specific Conventions

### File Organization
- `songs/` - MP3 files + `data/<song_name>.meta.json` analysis files + `data/<song_name>.actions.json` lighting actions
- `fixtures/fixtures.json` - Fixture definitions (RGB parcans, moving heads)
- `backend/models/` - Data models (app_state, actions_sheet, song_metadata, fixtures)
- `backend/services/` - Business logic (actions_service, dmx/, audio/, ollama/)

### DMX Canvas Time-Based Painting
```python
# Paint single frame at timestamp
canvas.paint_frame(time=5.2, channels={10: 255, 11: 128})

# Paint range with fade function
def fade_in(t): return {10: int(255 * t)}
canvas.paint_range(start=2.0, end=5.0, func=fade_in)
```

### Real-Time vs Pre-Rendered Approach
- **Pre-render**: Actions → DMX Canvas timeline for complex sequences
- **Real-time**: Direct WebSocket DMX updates for immediate control
- **Playback**: DMX Player reads canvas + sends Art-Net at 60fps

### Frontend Component Patterns
```jsx
// Preact hooks for real-time sync
const [currentTime, setCurrentTime] = useState(0);
const [songData, setSongData] = useState();

// WebSocket integration
useEffect(() => {
  wsSend("sync", {isPlaying, currentTime});
}, [isPlaying, syncTime]);

// WaveSurfer.js audio with seek integration
seekTo={(time) => handleSeekTo(time)}
```

## 🔍 Debugging & Testing

### Key Debug Files
- `integration_test.py` - Full workflow testing (analyze → actions → render → Art-Net)
- `artnet_dummy/` - Art-Net testing tools
- Browser DevTools WebSocket tab for real-time message inspection

### Common Debugging Commands
```python
# Check app state
print(f"Canvas duration: {app_state.dmx_canvas.duration}")
print(f"Fixtures: {list(app_state.fixtures.fixtures.keys())}")

# Validate actions
validation = actions_service.validate_actions(actions_sheet)
print(f"Valid: {validation['valid_actions']}/{validation['total_actions']}")
```

This system prioritizes real-time performance, modular fixture control, and AI-driven lighting generation while maintaining strict separation between analysis, action planning, and DMX rendering phases.

## 🛡️ Additional Enforcement Directives
4. **Testing Frameworks**
   - Do NOT install or use any external test frameworks (e.g., pytest, unittest, nose, etc.).
   - Use only the provided tests or create standalone Python scripts for testing and validation.
   
3. **Deprecated Cue/Timeline System**
   - Remove all references to cue and timeline systems, including:
     - Timeline/cue-related files, imports, functions, classes, comments, and variables.
     - Any mention of cues, timelines, or related legacy features in code, documentation, or comments.
   - If you encounter old methods or references, remove them (do not try to find alternatives or create missing files).

1. **Song Analysis Code Location**
   - All functions, classes, and logic related to song analysis must reside in the `song_analysis/` folder.
   - Do not place song analysis code in `backend/` or other folders.
   - Example: If implementing or updating song analysis features, always add or modify files in `song_analysis/`.

2. **Backend State Separation**
   - The global `app_state` singleton is strictly for backend DMX/light show state management.
   - Do not use or reference `app_state` in song analysis code or in the `song_analysis/` folder.

