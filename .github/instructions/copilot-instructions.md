# AI Light Show - Development Instructions for AI Coding Agents

## 🎯 Project Overview
AI-driven DMX lighting control system that analyzes music and creates synchronized light shows. Built with Python FastAPI backend and Preact/Vite frontend.

## 🧠 Core Architecture - Essential Mental Model

### Service Separation and Integration
The system follows a microservices-like architecture with clear separation of concerns:

1. **Backend Application** (`backend/`) - Main orchestration service
   - Coordinates all other services
   - Manages DMX control and fixture state
   - Handles WebSocket communication with frontend
   - Contains Ollama integration for AI features

2. **Song Analysis Service** (`song_analysis/`) - Standalone audio analysis
   - Completely separate from backend
   - Analyzes audio files for beats, patterns, sections
   - Provides REST API for backend to consume

3. **Frontend Application** (`frontend/`) - User interface
   - Preact/Vite application
   - Communicates with backend via WebSockets
   - Displays visualization and controls

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

## 🔧 Development Workflows

### Backend Development
```bash
# Setup
cd backend && pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Key entry points
backend/app.py              # FastAPI app with lifespan DMX player management
backend/models/app_state.py # Global singleton state - NEVER recreate
backend/services/websocket_manager.py # Core WebSocket manager
backend/services/websocket_handlers/ # Individual message handlers
```

### Song Analysis Service Development
```bash
# Setup
cd song_analysis && pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001 --reload

# Integration with backend
backend/services/song_analysis_client.py # Client for communicating with service
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

### Service Communication
```python
# Backend communicating with Song Analysis service
from backend.services.song_analysis_client import SongAnalysisClient

async with SongAnalysisClient() as client:
    analysis_result = await client.analyze_song(song_path)
```

### WebSocket Communication Protocol
Frontend ↔ Backend real-time sync:
```javascript
// Frontend patterns
wsSend("loadSong", { file: songFile });
wsSend("setDmx", { values: {10: 255, 11: 128} });
wsSend("userPrompt", { text: "flash red lights" });

// Backend handlers in websocket_handlers/
song_handler.py: _handle_load_song, _handle_analyze_song
dmx_handler.py: _handle_set_dmx
ai_handler.py: _handle_user_prompt
```

### Backend Progress Reporting Pattern
For any long-running backend operation, use the standardized progress reporting pattern:

```python
# Backend: Send progress updates during long operations
async def long_running_operation(websocket=None):
    total_steps = 100
    
    # Send initial progress
    if websocket:
        await websocket.send_json({
            "type": "backendProgress",
            "operation": "operationName",  # Unique identifier for this operation
            "progress": 0,
            "current": 0,
            "total": total_steps,
            "message": "Starting operation..."
        })
    
    for i in range(total_steps):
        # Do work...
        
        # Send progress update
        if websocket:
            await websocket.send_json({
                "type": "backendProgress",
                "operation": "operationName",
                "progress": int((i / total_steps) * 100),
                "current": i,
                "total": total_steps,
                "message": f"Processing step {i+1}/{total_steps}"
            })
    
    # Send completion
    if websocket:
        await websocket.send_json({
            "type": "backendProgress",
            "operation": "operationName",
            "progress": 100,
            "current": total_steps,
            "total": total_steps,
            "message": "Operation complete"
        })
```

```javascript
// Frontend: Handle progress in app.jsx
case "backendProgress": {
  if (msg.operation === "operationName") {
    setOperationProgress({
      isRunning: msg.progress < 100,
      progress: msg.progress || 0,
      current: msg.current || 0,
      total: msg.total || 0,
      message: msg.message || ""
    });
  }
  // Add more operations as needed
  break;
}
```

**Usage Guidelines:**
- Use `"backendProgress"` type for ALL long-running operations
- Include unique `operation` field to identify the specific process
- Always send initial (0%), intermediate, and completion (100%) progress
- Include descriptive `message` field for user feedback
- Handle errors by sending progress with `error: true` field

### Fixture Action Rendering
```python
# Create actions
action = ActionModel(
    fixture_id="parcan_l", 
    action="flash",
    start_time=5.2,
    parameters={"colors": ["blue"], "duration": 1.5}
)

# Add actions to the actions sheet
actions_sheet.add_action(action)

# IMPORTANT: Render to canvas AFTER adding all actions (not after each one)
# This optimizes performance by rendering once after bulk operations
actions_service = ActionsService(app_state.fixtures, app_state.dmx_canvas)
actions_service.render_actions_to_canvas(actions_sheet)
```
### IMPORTANT

#### 🔌 Fixture Behavior Model
DMX fixtures are dumb devices — they do not understand commands like "strobe" or "flash". They only respond to raw channel values over time.

#### Fixtures are static
DMX Fixtures are defined in `fixtures/fixtures.json` and can not be modified at runtime. 
Fixtures are static objects that represent physical devices with fixed channel mappings.

#### 🎬 Action-to-Channel Translation
All high-level lighting instructions — referred to as actions (e.g. "strobe", "fade_in", "seek") — must be converted into sequences of channel values over time by the system.

✅ Example: strobe Action
If channel 10 controls the shutter:
"strobe" → [
  (t=0.00, channel 10 = 255),
  (t=0.10, channel 10 = 0),
  (t=0.20, channel 10 = 255),
  ...
]

The DMX canvas must be painted explicitly with the right values at the right timestamps to simulate the effect.

#### 🧱 Implication
Lighting logic lives entirely in software. Fixtures are merely endpoints; the system is responsible for:
- Timing
- Value sequencing
- Effect shaping (e.g., ramping, pulsing, panning)

### Song Analysis Integration
```python
# Audio analysis with Essentia
song = SongMetadata(song_name="track.mp3", songs_folder=SONGS_DIR)
analyzed = song_analyze(song, reset_file=True)
# Creates: beats, chords, patterns, arrangement sections
```

## 🎵 Project-Specific Conventions

### File Organization
- `song_analysis/` - Standalone audio analysis service
- `backend/` - Main application and DMX control
  - `models/` - Data models (app_state, actions_sheet, song_metadata, fixtures)
  - `services/` - Business logic (actions_service, dmx/, ollama/)
  - `services/utils/` - Utility functions (broadcast.py)
  - `services/websocket_handlers/` - WebSocket message handlers
- `frontend/` - User interface
  - `src/components/` - UI components
  - `src/hooks/` - Custom React hooks
- `songs/` - MP3 files + `data/<song_name>.meta.json` analysis files + `data/<song_name>.actions.json` lighting actions
- `fixtures/fixtures.json` - Fixture definitions (RGB parcans, moving heads)

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

## 🛡️ Additional Enforcement Directives

1. **Service Separation**
   - **Backend Service** (`backend/`): 
     - Main application orchestration
     - DMX control, fixture management
     - AI/Ollama integration
     - WebSocket communication
     - Client interfaces to other services

   - **Song Analysis Service** (`song_analysis/`):
     - Completely separate from backend
     - All audio analysis code must be here
     - Provides REST API for backend to consume
     - No references to `app_state` or DMX components

2. **Integration Patterns**
   - Services communicate through dedicated client interfaces
   - Example: `backend/services/song_analysis_client.py` for song analysis

3. **Testing Frameworks**
   - Do NOT install or use any external test frameworks (e.g., pytest, unittest, nose, etc.).
   - Use only the provided tests or create standalone Python scripts for testing and validation.

4. **Song Analysis Code Location**
   - All functions, classes, and logic related to song analysis must reside in the `song_analysis/` folder.
   - Do not place song analysis code in `backend/` or other folders.
   - Example: If implementing or updating song analysis features, always add or modify files in `song_analysis/`.

5. **Backend State Separation**
   - The global `app_state` singleton is strictly for backend DMX/light show state management.
   - Do not use or reference `app_state` in song analysis code or in the `song_analysis/` folder.

6. **Action Rendering Performance**
   - When adding or modifying multiple actions, render them to the canvas only ONCE after all changes are complete.
   - Do NOT render after each individual action is added or modified.
   - Example pattern for bulk operations:
     ```python
     # Add multiple actions
     for time_point in beat_times:
         action = ActionModel(...)
         actions_sheet.add_action(action)
     
     # Render only ONCE at the end
     actions_service.render_actions_to_canvas(actions_sheet)
     ```

This system prioritizes modular services, clear separation of concerns, real-time performance, and AI-driven lighting generation while maintaining strict boundaries between analysis, action planning, and DMX rendering phases.

