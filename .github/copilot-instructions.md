# Copilot Instructions for AI Light Show

## Project Overview
- **AI Light Show** is a multi-service system for music-driven DMX lighting control, combining audio analysis, AI reasoning, and real-time visualization.
- Major components:
  - `backend/`: FastAPI app, agent orchestration, DMX control
  - `song_analysis/`: Audio analysis (Essentia, Demucs)
  - `frontend/`: React/Preact UI, WebSocket chat, visualization
  - `fixtures/`: Lighting fixture definitions
  - `logs/`: Pipeline and agent outputs for debugging

## Key Architectural Patterns
- **3-Agent Pipeline** (LangGraph):
  1. `ContextBuilderAgent` (Mixtral): interprets musical segments
  2. `LightingPlannerAgent` (Mixtral): proposes lighting actions
  3. `EffectTranslatorAgent` (Command-R): generates DMX commands
- Agents are unified in `backend/services/agents/` and support both LangGraph and legacy workflows.
- All agent state is passed as a TypedDict (`PipelineState`).
- Dynamic fixture/channel info: always use `app_state.fixtures` (see `dynamic_effect_translator_summary.md`).

## Developer Workflows
- **Build/Run**:
  - Use `docker-compose up --build` for full stack
  - For dev: run backend, frontend, and services separately (see README)
- **Testing**:
  - Run `python test_lighting_pipeline.py` for pipeline tests
  - Use `python pipeline_integration_example.py` for integration
- **Debugging**:
  - Check logs in `logs/` for agent outputs and errors
  - Use health checks: `python backend/health_check_service.py`

## Conventions & Patterns
- **Direct Commands**: Chat input supports `#` commands for manual DMX control (see `docs/direct_commands.md`)
- **No Hardcoded Fixtures**: Always extract fixture/channel info dynamically
- **Error Handling**: Agents log errors and preserve partial results
- **Frontend**: Uses Tailwind CSS, React/Preact, and WebSocket for real-time updates
- **Song Analysis**: Results cached, large files may require more RAM

## Integration Points
- **WebSocket**: Real-time chat and control between frontend and backend
- **REST API**: `/api/ai`, `/songs`, `/fixtures`, `/dmx/update` (see `docs/architecture-details.md`)
- **External Services**: Ollama LLM, Song Analysis (configurable via env vars)

## Examples
- See `docs/agent-architecture.md` and `docs/langgraph-pipeline.md` for agent usage and pipeline examples
- See `docs/direct_commands.md` for supported chat commands
- See `fixtures/fixtures.json` for fixture config pattern

---
**Edit this file to update agent instructions. For questions, see README and docs/.**
