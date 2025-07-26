# AI Light Show - Copilot Instructions

## Core System
Multi-service DMX lighting control: `backend/` (FastAPI, agents, DMX), `song_analysis/` (audio analysis), `frontend/` (Preact UI, WebSocket).

## Critical Patterns
- **Agents**: Unified in `backend/services/agents/` - `ContextBuilderAgent`, `LightingPlannerAgent`, `EffectTranslatorAgent`
- **State**: Always use global `app_state` singleton - never recreate instances
- **Current Song**: Backend only - `app_state.current_song` (SongMetadata object)
- **Fixtures**: Dynamic only - use `app_state.fixtures`, no hardcoded values
- **Actions**: Bulk render after all changes: `actions_service.render_actions_to_canvas(actions_sheet)`

## Service Separation
- **Backend**: DMX control, WebSocket, agent orchestration
- **Song Analysis**: Standalone service, REST API, no `app_state` usage
- **Frontend**: WebSocket communication, real-time visualization

## Development
```bash
# Full stack
docker-compose up --build

# Individual services  
cd backend && uvicorn app:app --port 8000 --reload
cd song_analysis && uvicorn app:app --port 8001 --reload
cd frontend && npm run dev
```

## Key Files
- `backend/models/app_state.py` - Global state (NEVER recreate)
- `backend/services/agents/` - All AI agents (unified location)
- `backend/services/websocket_handlers/` - Message handlers
- `fixtures/fixtures.json` - Fixture definitions (static)

## Implementation Patterns

### Current Song Access (Backend Only)
```python
from ...models.app_state import app_state
from ...models.song_metadata import SongMetadata

if not app_state.current_song:
    raise ValueError("No song is currently loaded")
song: SongMetadata = app_state.current_song
```

### Service Communication
```python
# Backend ↔ Song Analysis
from backend.services.song_analysis_client import SongAnalysisClient
async with SongAnalysisClient() as client:
    result = await client.analyze_song(song_path)
```

### WebSocket Patterns
```javascript
// Frontend
wsSend("loadSong", { file: songFile });
wsSend("userPrompt", { text: "flash red lights" });

// Backend handlers in websocket_handlers/
song_handler.py, dmx_handler.py, ai_handler.py
```

### Progress Reporting
```python
# Long operations
await websocket.send_json({
    "type": "backendProgress",
    "operation": "operationName",
    "progress": 50,
    "current": 5,
    "total": 10,
    "message": "Processing..."
})
```

### Agent Usage
```python
# Unified agents
from backend.services.agents import ContextBuilderAgent, LightingPlannerAgent, EffectTranslatorAgent

# LangGraph pipeline
agent = ContextBuilderAgent(model="mixtral")
result = agent.run(pipeline_state)

# Direct API calls
response = agent.get_context(prompt)
```

### LangGraph Pipelines (Two Separate)

**Song Analysis Pipeline** (`song_analysis/`): Audio analysis
```python
from song_analysis.simple_pipeline import run_pipeline
result = run_pipeline('/path/to/song.mp3')
```

**Lighting Design Pipeline** (`backend/`): Musical segments → lighting actions
```python
from backend.services.langgraph.lighting_pipeline import run_lighting_pipeline
result = run_lighting_pipeline(segment_input)
```

## DMX & Fixtures
- Fixtures are static (fixtures.json) - no runtime modification
- DMX devices only understand channel values over time
- Actions (strobe, flash) → channel sequences by software
- Canvas painting: `canvas.paint_frame(time=5.2, channels={10: 255})`

## Testing & Debug
```bash
python test_lighting_pipeline.py
python -m song_analysis.test_pipeline_run --song track.mp3
# Check logs/ directory for pipeline outputs
```

## Enforcement
- No hardcoded placeholders when moving code
- User prompts ALWAYS be handled by LLM (NO HARDCODED LOGIC, except for direct commands)
- Do NOT create backward compatibility, update to latest patterns if needed.
- Do not create tests, think in the chat context and then implement the code directly.
- Do not use fallbacks or legacy patterns
- prepend "clear &&" to test commands.
- Always use class public properties, not private or internal
- Use latest import paths from `backend/services/agents/`
- Service boundaries: backend ↔ song_analysis via REST client only
- Service boundaries: backend ↔ frontend via WebSocket only
- LangGraph pipelines: Song analysis (audio) vs Lighting design (actions) - separate purposes

---
**Edit this file to update agent instructions. For questions, see README and docs/.**
