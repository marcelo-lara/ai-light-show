# Comprehensive AI Light Show Project Instructions for Copilot LLM

## 📋 Project Overview

The AI Light Show is an intelligent DMX lighting control system that uses AI to analyze music and create synchronized light shows. The system combines audio analysis and natural language processing to automatically generate lighting performances that match musical content.

**Architecture**: Modern full-stack application with Python FastAPI backend and Preact/Vite frontend.

## 🚨 Critical Development Guidelines

### 1. **NO Re-initialization of Classes**
- **NEVER** re-initialize existing class instances unless absolutely necessary
- Use existing instances from `app_state` global object:
  ```python
  from backend.models.app_state import app_state
  # Use app_state.dmx_canvas, app_state.fixtures, etc.
  ```
- Before creating new instances, check if they already exist in `app_state`

### 2. **NO Backwards Compatibility**
- Ignore all deprecated/removed functionality
- Do not attempt to maintain or restore old systems
- Focus on current architecture only

### 3. **When Components are Refactored**
- **DO NOT** search for "old alternatives" to similar methods
- If old method doesn't exist, add clear comment explaining the situation
- Example:
  ```python
  # NOTE: Old cue system removed - no direct replacement for this functionality
  # Use the new Actions system instead
  ```

## 🏗️ Current Architecture (Post-Refactor)

### Core Components

#### Backend (Python/FastAPI)
- **App State Management** (`backend/models/app_state.py`): Centralized state with global `app_state` instance
- **DMX Canvas** (`backend/services/dmx/dmx_canvas.py`): Timeline-based DMX universe management
- **DMX Player** (`backend/services/dmx/dmx_player.py`): Real-time playback engine
- **Fixtures System** (`backend/models/fixtures/`): Object-oriented fixture control
- **Actions System** (`backend/models/actions_sheet.py`): NEW - Replaces deprecated cue system
- **Audio Analysis** (`backend/services/audio/`): Essentia-based audio processing
- **AI Integration** (`backend/services/ollama/`): Local LLM for lighting suggestions

#### Frontend (Preact/Vite)
- **Audio Player** (`frontend/src/AudioPlayer.jsx`): Waveform visualization with WaveSurfer.js
- **Chat Assistant** (`frontend/src/ChatAssistant.jsx`): Natural language interface
- **Song Analysis** (`frontend/src/components/song/SongAnalysis.jsx`): Audio analysis visualization
- **Fixtures Control** (`frontend/src/components/fixtures/`): Real-time fixture monitoring
- **Actions Card** (`frontend/src/components/ActionsCard.jsx`): NEW - Displays lighting actions

## 🚫 DEPRECATED SYSTEMS (DO NOT USE)

### ❌ Timeline/Cue System (COMPLETELY REMOVED)
- **Files Removed**: `timeline_engine.py`, `cue_service.py`, `SongCues.jsx`
- **Functionality Removed**: Timeline-based cue editing, cue management, cue preview
- **Comments in Code**: Look for `DEPRECATED:` and `# DEPRECATED:` comments
- **Frontend**: All cue-related UI components removed
- **Backend**: All cue-related API endpoints removed

### ❌ What NOT to Reference
```python
# ❌ NEVER use these (removed):
from backend.services.cue_service import CueService  # REMOVED
from backend.timeline_engine import TimelineEngine   # REMOVED

# ❌ NEVER use these frontend components:
import SongCues from './SongCues.jsx'              # REMOVED
import PresetSelector from './PresetSelector.jsx'  # REMOVED (partially)
```

## ✅ CURRENT SYSTEM ARCHITECTURE

### 1. DMX Canvas System
```python
# Singleton instance - DO NOT recreate
from backend.models.app_state import app_state
canvas = app_state.dmx_canvas  # Use existing instance

# Canvas operations
canvas.paint_frame(time, {channel: value})
canvas.paint_range(start_time, end_time, fade_function)
frame_data = canvas.get_frame(time)
```

### 2. Fixtures System
```python
# Use existing fixtures instance
fixtures = app_state.fixtures  # FixturesListModel instance

# Get specific fixture
fixture = fixtures.get_fixture("parcan_l")

# Render actions to fixtures
fixture.render_action("flash", {"colors": ["red"], "duration": 1.0})
```

### 3. Actions System (NEW - Replaces Cues)
```python
from backend.models.actions_sheet import ActionsSheet, ActionModel
from backend.services.actions_service import ActionsService

# Create actions sheet for a song
actions_sheet = ActionsSheet(song_name="example.mp3")

# Add action
action = ActionModel(
    fixture_id="parcan_l",
    action_type="flash",
    start_time=5.2,
    parameters={"colors": ["blue"], "duration": 1.5}
)
actions_sheet.add_action(action)

# Render to canvas
actions_service = ActionsService(fixtures, dmx_canvas)
actions_service.render_actions_to_canvas(actions_sheet)
```

### 4. Audio Analysis
```python
from backend.models.song_metadata import SongMetadata
from backend.services.audio.song_analyze import song_analyze

# Load and analyze song
song = SongMetadata(song_name="example.mp3", songs_folder="/path/to/songs")
analyzed_song = song_analyze(song, reset_file=True)

# Access analysis results
beats = analyzed_song.beats
chords = analyzed_song.chords
patterns = analyzed_song.patterns
```

### 5. DMX Player (Real-time Playback)
```python
from backend.services.dmx.dmx_player import dmx_player

# Control playback
dmx_player.play()
dmx_player.pause()
dmx_player.seek(time_seconds)

# Check status
status = dmx_player.playback_state
current_time = status.get_current_time()
is_playing = status.is_playing
```

## 🔧 Common Development Patterns

### Working with App State
```python
from backend.models.app_state import app_state

# Always use existing instances
dmx_canvas = app_state.dmx_canvas
fixtures = app_state.fixtures
current_song = app_state.current_song

# Update state
app_state.current_song_file = "new_song.mp3"
app_state.current_song = new_song_metadata
```

### Fixture Operations
```python
# Get fixture
fixture = app_state.fixtures.get_fixture("parcan_l")

# Check if fixture exists before using
if fixture:
    fixture.render_action("flash", {"duration": 2.0})
else:
    print(f"Fixture not found: parcan_l")
```

### WebSocket Communication (Frontend)
```javascript
// Send commands to backend
wsSend("loadSong", { file: songFile });
wsSend("analyzeSong", { songFile: currentSongFile });
wsSend("setDmx", { values: channelMap });
wsSend("blackout", {});

// Handle responses
case "analyzeResult":
    setAnalysisResult({"status": msg.status});
    if (msg.metadata) setSongData(msg.metadata);
    break;

case "actionsUpdate":
    setLightingActions(msg.actions || []);
    break;
```

## 📁 File Structure Guide

### Backend Structure
```
backend/
├── models/
│   ├── app_state.py          # ✅ Global state management
│   ├── actions_sheet.py      # ✅ NEW - Actions system
│   ├── song_metadata.py      # ✅ Song analysis data
│   └── fixtures/            # ✅ Fixture object model
├── services/
│   ├── dmx/                 # ✅ DMX canvas and player
│   ├── audio/               # ✅ Audio analysis
│   ├── ollama/              # ✅ AI integration
│   ├── actions_service.py   # ✅ NEW - Actions rendering
│   └── websocket_service.py # ✅ WebSocket handling
├── routers/
│   ├── songs.py            # ✅ Song management
│   └── ai_router.py        # ✅ AI chat interface
└── app.py                  # ✅ FastAPI application
```

### Frontend Structure
```
frontend/src/
├── app.jsx                 # ✅ Main application
├── AudioPlayer.jsx         # ✅ Audio playback
├── ChatAssistant.jsx       # ✅ AI chat interface
├── components/
│   ├── fixtures/           # ✅ Fixture controls
│   ├── song/               # ✅ Song analysis UI
│   └── ActionsCard.jsx     # ✅ NEW - Actions display
└── ...
```

## 🚨 Error Prevention

### Common Mistakes to Avoid
1. **Creating new DMX canvas instances**
   ```python
   # ❌ WRONG
   dmx_canvas = DmxCanvas()
   
   # ✅ CORRECT
   dmx_canvas = app_state.dmx_canvas
   ```

2. **Trying to use removed cue system**
   ```python
   # ❌ WRONG - This system was removed
   from backend.services.cue_service import CueService
   
   # ✅ CORRECT - Use actions system
   from backend.services.actions_service import ActionsService
   ```

3. **Re-initializing fixtures**
   ```python
   # ❌ WRONG
   fixtures = FixturesListModel(config_file, canvas)
   
   # ✅ CORRECT
   fixtures = app_state.fixtures
   ```

### When You Can't Find Old Methods
```python
# If old method doesn't exist, add comment like this:
# NOTE: Previous timeline_engine.add_cue() method removed
# Use ActionsSheet.add_action() from new actions system instead
```

## 🔌 Integration Points

### AI Chat → Actions System
```python
# AI generates action commands like:
"flash parcan_l blue at 5.2s for 1.5s with intensity 0.8"

# Parsed by ActionsParserService into:
ActionModel(
    fixture_id="parcan_l",
    action_type="flash", 
    start_time=5.2,
    parameters={"colors": ["blue"], "duration": 1.5, "intensity": 0.8}
)
```

### Song Analysis → Actions Generation
```python
# Use song analysis to create actions
song = app_state.current_song
if song and song.beats:
    for beat in song.beats:
        if beat.energy > 0.8:  # High energy beat
            action = ActionModel(
                fixture_id="all_parcans",
                action_type="flash",
                start_time=beat.time,
                parameters={"duration": 0.5}
            )
```

## 🎯 Development Workflow

1. **Always check app_state first** for existing instances
2. **Use the Actions system** instead of the removed cue system
3. **Follow the DMX Canvas → Fixtures → Actions flow**
4. **Add deprecation comments** when old methods don't exist
5. **Test with existing song files** in `/songs` directory
6. **Use WebSocket for real-time communication**

## 📊 Key Data Models

### SongMetadata Structure
```python
{
    "song_name": "example.mp3",
    "duration": 240.5,
    "bpm": 128.0,
    "beats": [{"time": 0.5, "energy": 0.8}, ...],
    "chords": [{"time": 0.0, "chord": "Am"}, ...],
    "patterns": {"drums": [...], "vocals": [...]},
    "arrangement": {"intro": Section(...), "verse1": Section(...)},
    "key_moments": [{"time": 32.0, "name": "Drop", "description": "Main drop"}]
}
```

### ActionModel Structure
```python
{
    "fixture_id": "parcan_l",
    "action_type": "flash",  # flash, fade, strobe, etc.
    "start_time": 5.2,
    "duration": 1.5,
    "parameters": {"colors": ["blue"], "intensity": 0.8}
}
```

This guide ensures consistent development while avoiding deprecated systems and unnecessary re-initialization of core components.
