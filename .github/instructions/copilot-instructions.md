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

### Accessing Current Song Pattern
When accessing the current song from app_state in backend code, always follow this exact pattern:
```python
# Get the current song (SongMetadata) from app state
from ...models.app_state import app_state
from ...models.song_metadata import SongMetadata

if not app_state.current_song:
    raise ValueError("No song is currently loaded")
song: SongMetadata = app_state.current_song
```
**IMPORTANT**: 
- This pattern applies only to backend code
- Don't try to parse folder names or other song-related data directly
- Always access properties through the SongMetadata object
- The song_analysis service does not use app_state

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

With the LangGraph pipeline, the Song Analysis step now follows this modular flow:
```
MP3 File → [Stem Split → Beat Detect → Pattern Analysis → Segment Labeler (LLM) → Lighting Hint Generator (LLM)] → Song Metadata → Backend
```

Each node in the LangGraph pipeline logs its input/output to JSON files in the `logs/` directory, enabling easier debugging and tracing of the analysis process.

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

### LangGraph Pipeline in Song Analysis
The song_analysis service uses a LangGraph-based pipeline for modular, traceable audio analysis:

```python
# Using the LangGraph pipeline
from song_analysis.simple_pipeline import run_pipeline

# Run the pipeline on a song file
pipeline_results = run_pipeline('/path/to/song.mp3')

# Pipeline output format
{
  "sections": [
    { "name": "Intro", "start": 0.0, "end": 12.0 },
    { "name": "Drop", "start": 34.2, "end": 36.7 }
  ],
  "lighting_hints": [
    { "section_name": "Drop", "suggestion": "Flash red with strobe" }
  ]
}
```

Key components in the LangGraph pipeline:
1. `song_analysis/langgraph_pipeline.py`: Main LangGraph pipeline definition
2. `song_analysis/simple_pipeline.py`: Fallback pipeline when LangGraph isn't available
3. `song_analysis/test_pipeline_run.py`: Test runner for the pipeline
4. `song_analysis/services/legacy_analyzer.py`: Legacy procedural analysis for fallback

The pipeline creates JSON output logs in the `logs/` directory for each node, enabling easier debugging and tracing.

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

### Current Song Access Pattern
Always access the current song in the backend using this standardized pattern:
```python
# Get the current song (SongMetadata) from app state
from ...models.app_state import app_state
from ...models.song_metadata import SongMetadata

if not app_state.current_song:
    raise ValueError("No song is currently loaded")
song: SongMetadata = app_state.current_song

# Then access properties through the SongMetadata object
print(f"Processing song: {song.title}")
```
**NOTE**: This pattern applies only to backend code. The song_analysis service does not use app_state.

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

### Background Processing for Long Operations
For very long operations, run them in the background to avoid blocking the UI:

```python
# Backend: Run long operations in background
async def handle_long_operation_command(websocket):
    import asyncio
    
    async def run_operation():
        try:
            result = await long_running_operation(websocket=websocket)
            await websocket.send_json({
                "type": "operationResult",
                "status": "ok",
                "result": result
            })
        except Exception as e:
            await websocket.send_json({
                "type": "operationResult", 
                "status": "error",
                "message": str(e)
            })
    
    # Start background task
    asyncio.create_task(run_operation())
    
    # Return immediately to user
    return True, "Operation started in background. Check progress above.", None
```

This pattern allows:
- Non-blocking command execution
- Immediate user feedback that operation has started
- Progress updates during execution
- Final result notification when complete

### Persistent Background Tasks (Survives Browser Disconnection)
For critical long-running operations that must continue even if the user closes the browser, use the persistent task tracking system:

```python
# Backend: Create persistent background task
from backend.models.app_state import app_state
import uuid

async def handle_persistent_operation_command(websocket):
    # Generate unique task ID
    task_id = f"operation_name_{uuid.uuid4().hex[:8]}"
    
    async def run_persistent_operation():
        try:
            # Create task state for tracking
            task_state = app_state.create_background_task(
                task_id=task_id,
                song_name="current_song",
                operation="operationName",
                total=100  # Total steps/chunks
            )
            
            # Your long operation here with progress updates
            for i in range(100):
                # Update progress in app_state
                app_state.update_task_progress(
                    task_id, 
                    progress=int((i/100)*100),
                    current=i,
                    message=f"Processing step {i}/100"
                )
                
                # Broadcast to ALL connected clients (resilient to disconnections)
                app_state.broadcast_to_clients({
                    "type": "backendProgress",
                    "operation": "operationName",
                    "task_id": task_id,
                    "progress": int((i/100)*100),
                    "current": i,
                    "total": 100,
                    "message": f"Processing step {i}/100"
                })
                
                # Your actual work here
                await asyncio.sleep(0.1)
            
            # Mark as completed
            app_state.complete_task(task_id, result="operation_result")
            
            # Broadcast final result
            app_state.broadcast_to_clients({
                "type": "operationResult",
                "status": "ok",
                "task_id": task_id,
                "message": "Operation completed successfully"
            })
            
        except Exception as e:
            # Mark as failed
            app_state.complete_task(task_id, error=str(e))
            app_state.broadcast_to_clients({
                "type": "operationResult",
                "status": "error", 
                "task_id": task_id,
                "message": str(e)
            })
    
    # Start background task and store reference
    task = asyncio.create_task(run_persistent_operation())
    if task_id in app_state.background_tasks:
        app_state.background_tasks[task_id].task = task
    
    return True, f"Persistent operation started (Task ID: {task_id}). Will continue even if browser is closed.", None
```

**Key Features:**
- Tasks survive browser disconnections
- Progress is broadcast to all connected clients
- Task state is tracked in global app_state
- Unique task IDs for tracking multiple operations
- Use `#tasks` command to check status of background operations

**When to Use:**
- Long audio analysis operations (>30 seconds)
- File processing that takes significant time  
- Any operation where user might close browser before completion
- Operations that benefit from persistence across sessions

### Checkpoint Resume Pattern for Long Operations
For very long operations that may be interrupted, implement checkpoint/resume functionality:

```python
# Load existing progress from checkpoint file
existing_progress = []
last_processed_item = -1

if checkpoint_file.exists():
    try:
        with open(checkpoint_file, 'r') as f:
            checkpoint_data = json.load(f)
        existing_progress = checkpoint_data.get('results', [])
        last_processed_item = checkpoint_data.get('last_processed_item', -1)
        print(f"🔄 Resuming from item {last_processed_item + 1}")
    except Exception:
        print("⚠️ Could not read checkpoint, starting fresh")

# Process items starting from resume point
start_index = last_processed_item + 1
for i in range(start_index, len(all_items)):
    # Process item
    result = process_item(all_items[i])
    results.append(result)
    
    # Save checkpoint every N items
    if (i + 1) % 5 == 0:
        checkpoint_data = {
            "results": results,
            "last_processed_item": i,
            "total_items": len(all_items),
            "progress_percent": int(((i + 1) / len(all_items)) * 100)
        }
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
```

**Benefits:**
- Resilient to interruptions and crashes
- No lost work if process is stopped
- Can resume exactly where it left off
- Periodic saves prevent data loss

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

### LangGraph Pipelines - Two Separate Implementations

The project has TWO distinct LangGraph pipelines in different services:

#### 1. Song Analysis Pipeline (song_analysis/)
Used for audio analysis and musical feature extraction with these nodes:

1. **stem_split**: Separates audio into stems using Demucs
2. **beat_detect**: Identifies beats and tempo using Essentia
3. **pattern_analysis**: Finds recurring patterns in the audio
4. **segment_labeler**: Uses LLM to label segments (Intro, Verse, etc.)
5. **lighting_hint_generator**: Uses LLM to suggest lighting effects

```python
# In the song_analysis service
# The SongAnalyzer will automatically use LangGraph with fallback to legacy
from song_analysis.services.audio_analyzer import SongAnalyzer

analyzer = SongAnalyzer()
result = analyzer.analyze(song_metadata, reset_file=True)

# Direct pipeline usage
from song_analysis.simple_pipeline import run_pipeline

pipeline_results = run_pipeline(song_path)
print(f"Found {len(pipeline_results['sections'])} sections")
print(f"Generated {len(pipeline_results['lighting_hints'])} lighting hints")

# The output follows this structure:
{
  "sections": [
    {"name": "Intro", "start": 0.0, "end": 12.0},
    {"name": "Verse", "start": 12.0, "end": 34.2},
    {"name": "Drop", "start": 34.2, "end": 36.7}
  ],
  "lighting_hints": [
    {"section_name": "Drop", "start": 34.2, "end": 36.7, "suggestion": "Flash red with strobe"}
  ]
}
```

#### 2. Lighting Design Pipeline (backend/)
Used for AI-driven lighting design generation from musical segments with these agents:

1. **Context Builder**: Interprets musical segments into natural language summaries (Mixtral)
2. **Lighting Planner**: Creates high-level lighting actions from context (Mixtral)
3. **Effect Translator**: Translates actions into specific DMX commands (Command-R)

```python
# Using the lighting design LangGraph pipeline
from backend.services.langgraph.lighting_pipeline import run_lighting_pipeline

# Run the 3-agent pipeline on a musical segment
segment_input = {
    "segment": {
        "name": "Drop",
        "start": 34.2,
        "end": 36.7,
        "features": {"energy": 0.9, "tempo": 128}
    }
}

result = run_lighting_pipeline(segment_input)

# Pipeline output format
{
  "segment": {...},
  "context_summary": "High energy climax with heavy bass",
  "actions": [
    {"type": "strobe", "color": "white", "start": 34.2, "duration": 2.5}
  ],
  "dmx": [
    {"fixture": "parcan_l", "channel": 10, "value": 255, "time": 34.2}
  ]
}

# Individual agent usage
from backend.services.langgraph.agents import ContextBuilderAgent, LightingPlannerAgent, EffectTranslatorAgent

context_agent = ContextBuilderAgent(model="mixtral")
planner_agent = LightingPlannerAgent(model="mixtral")
translator_agent = EffectTranslatorAgent(model="command-r", fallback_model="mixtral")

# Use agents individually for testing or partial execution
result = context_agent.run(pipeline_state)

# Partial pipeline execution (skip context building)
state_with_context = {
    "segment": segment_data,
    "context_summary": "Pre-generated context",
    "actions": [],
    "dmx": []
}
planner_result = planner_agent.run(state_with_context)
final_result = translator_agent.run(planner_result)

# Custom error handling per agent
def robust_agent_execution(agent, state):
    try:
        return agent.run(state)
    except Exception as e:
        print(f"Agent {agent.__class__.__name__} failed: {e}")
        error_state = state.copy()
        error_state["error"] = str(e)
        return error_state
```

**Benefits of Modular Agent Design**:
- **Independent Testing**: Each agent can be tested individually
- **Flexible Configuration**: Different models per agent
- **Better Error Isolation**: Issues in one agent don't affect others
- **Easy Extension**: New agents can be added without modifying existing code
- **Partial Execution**: Can start pipeline from any agent
- **Reusability**: Agents can be used in different contexts
```

**CRITICAL SEPARATION**: These are completely separate pipelines with different purposes:
- **Song Analysis Pipeline** (`song_analysis/`): Analyzes MP3 files → Musical features and sections
- **Lighting Design Pipeline** (`backend/`): Takes musical segments → Generates lighting commands

Key file locations:
- Song Analysis: `song_analysis/langgraph_pipeline.py`, `song_analysis/simple_pipeline.py`
- Lighting Design: `backend/services/langgraph/lighting_pipeline.py`, `backend/services/langgraph/agents/`

Both pipelines create JSON output logs in the `logs/` directory for each node, enabling easier debugging and tracing.

## 🎵 Project-Specific Conventions

### File Organization
- `song_analysis/` - Standalone audio analysis service
  - `langgraph_pipeline.py` - LangGraph-based modular analysis pipeline
  - `simple_pipeline.py` - Simplified pipeline with fallback mechanism
  - `test_pipeline_run.py` - Pipeline test runner
  - `services/` - Audio analysis components and LLM integration
  - `services/legacy_analyzer.py` - Traditional procedural analysis (fallback)
  - `services/audio/` - Core audio analysis modules (essentia, demucs, pattern detection)
- `backend/` - Main application and DMX control
  - `models/` - Data models (app_state, actions_sheet, song_metadata, fixtures)
  - `services/` - Business logic (actions_service, dmx/, ollama/)
  - `services/utils/` - Utility functions (broadcast.py)
  - `services/langgraph/` - AI lighting design pipeline
    - `lighting_pipeline.py` - Main pipeline orchestration
    - `agents/` - Modular agent implementations
      - `context_builder.py` - Musical context interpretation agent
      - `lighting_planner.py` - Lighting action planning agent
      - `effect_translator.py` - DMX command translation agent
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

### LangGraph Pipeline Debugging
```python
# Test the pipeline directly
python -m song_analysis.test_pipeline_run --song born_slippy.mp3

# Examine node outputs
import json
from pathlib import Path

# Load and inspect any node's output
with open(Path("logs") / "beat_detect.json", "r") as f:
    beat_output = json.load(f)
    print(f"Detected {len(beat_output.get('beats', []))} beats")

# Inspect the final output
with open(Path("logs") / "final_output.json", "r") as f:
    final_output = json.load(f)
    print(f"Found {len(final_output.get('sections', []))} sections")
    print(f"Generated {len(final_output.get('lighting_hints', []))} lighting hints")
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

6. **Current Song Access Pattern (Backend Only)**
   - When accessing the current song from app_state in backend code, strictly follow this pattern:
   ```python
   # Get the current song (SongMetadata) from app state
   from ...models.app_state import app_state
   from ...models.song_metadata import SongMetadata
   
   if not app_state.current_song:
       raise ValueError("No song is currently loaded")
   song: SongMetadata = app_state.current_song
   ```
   - This pattern applies only to backend code; it should not be used in the song_analysis service.
   - Do not try to parse folder names or file paths directly to access song data.
   - Always use the SongMetadata object's properties and methods to access song information.
   - Check that app_state.current_song exists before attempting to use it.

7. **Action Rendering Performance**
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

8. **LangGraph Pipeline Development**
   **CRITICAL**: Two separate LangGraph implementations exist - do not mix them:
   
   **Song Analysis Pipeline** (`song_analysis/`):
   - Always follow the modular LangGraph design when adding new audio analysis features.
   - Create new nodes that take a single input dictionary and return a single output dictionary.
   - Log node inputs/outputs using the `log_node_output` utility function.
   - Ensure each node can function independently for better debugging and testing.
   - Always include a fallback mechanism for when LangGraph is not available.
   
   **Lighting Design Pipeline** (`backend/services/langgraph/`):
   - Use modular agent classes in separate files: `agents/context_builder.py`, `agents/lighting_planner.py`, `agents/effect_translator.py`
   - Each agent should be self-contained and independently testable
   - Use TypedDict for PipelineState schema consistency
   - Maintain LangGraph compatibility through wrapper functions (`run_context_builder`, etc.)
   - Always provide fallback sequential execution when LangGraph is unavailable
   
   Example lighting agent implementation:
   ```python
   # In backend/services/langgraph/agents/my_agent.py
   class MyLightingAgent:
       def __init__(self, model: str = "mixtral"):
           self.model = model
       
       def run(self, state: PipelineState) -> PipelineState:
           # Agent logic here
           result_state = state.copy()
           result_state["my_output"] = my_processing(state)
           return result_state
   
   # LangGraph wrapper function
   def run_my_agent(state: PipelineState) -> PipelineState:
       agent = MyLightingAgent()
       return agent.run(state)
   ```
   
   **Never mix the two pipelines**: Song analysis creates musical features; lighting design consumes them.

This system prioritizes modular services, clear separation of concerns, real-time performance, and AI-driven lighting generation while maintaining strict boundaries between analysis, action planning, and DMX rendering phases.

