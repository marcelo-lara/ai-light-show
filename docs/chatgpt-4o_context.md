# ChatGPT 4o Context for AI Light Show

## Project Overview
The AI Light Show project is a multi-service system designed for music-driven DMX lighting control. It combines audio analysis, AI reasoning, and real-time visualization. Below is an analysis of the project structure and its components.

## Folder Structure and Key Components

### 1. `backend/`
- **Purpose**: Hosts the FastAPI application, agent orchestration, and DMX control logic.
- **Subfolders**:
  - `models/`: Contains data models such as `app_state`.
  - `routers/`: Defines API routes for the application.
  - `services/`: Implements core services like agents and WebSocket handlers.
  - `tests/`: Includes unit tests for backend functionality.
- **Key Files**:
  - `app.py`: Entry point for the FastAPI application.
  - `dmx_controller.py`: Manages DMX lighting control.
  - `health_check_service.py`: Provides health checks for the backend.

### 2. `frontend/`
- **Purpose**: Implements the user interface using React/Preact and Tailwind CSS.
- **Subfolders**:
  - `src/`: Contains React components and application logic.
  - `public/`: Static assets for the frontend.
- **Key Files**:
  - `ChatAssistant.jsx`: Handles real-time chat and LLM interactions.
  - `AudioPlayer.jsx`: Manages audio playback and visualization.

### 3. `song_analysis/`
- **Purpose**: Provides audio analysis services using libraries like Essentia and Demucs.
- **Key Features**:
  - Beat detection, BPM analysis, and chord detection.
  - AI-powered audio stem separation.
  - Integration with the LangGraph pipeline for segment labeling and lighting hints.

### 4. `fixtures/`
- **Purpose**: Defines lighting fixture configurations.
- **Key Files**:
  - `fixtures.json`: JSON file containing fixture definitions.

### 5. `docs/`
- **Purpose**: Contains documentation for the project.
- **Key Files**:
  - `agent-architecture.md`: Details the architecture of the agents.
  - `langgraph-pipeline.md`: Explains the LangGraph 3-agent pipeline.
  - `dynamic_effect_translator_summary.md`: Describes dynamic fixture and channel handling.

### 6. `logs/`
- **Purpose**: Stores logs for debugging and analysis.
- **Key Files**:
  - `beat_detect.json`: Logs related to beat detection.
  - `full_song_lighting_design.json`: Logs for the complete lighting design.

### 7. `tests/`
- **Purpose**: Includes test scripts for various components.
- **Key Files**:
  - `test_lighting_pipeline.py`: Tests the lighting pipeline.
  - `test_context.py`: Verifies dynamic context building.
  - `test_llm_status_sync.py`: Tests LLM status synchronization.

## Key Architectural Patterns

### LangGraph 3-Agent Pipeline
1. **Context Builder Agent**:
   - Interprets musical segments and builds a natural language context summary.
2. **Lighting Planner Agent**:
   - Proposes high-level lighting actions based on the context.
3. **Effect Translator Agent**:
   - Converts lighting actions into specific DMX commands.

### Singleton Pattern
- **DMX Canvas**:
  - Ensures a single instance of the DMX canvas is used across the application.
  - Allows shared state and consistent parameter updates.

## Integration Points
- **WebSocket**: Enables real-time communication between the frontend and backend.
- **REST API**: Provides endpoints for AI, song analysis, and DMX updates.
- **External Services**: Integrates with Ollama LLM and audio analysis tools.

## Developer Workflows
- **Build/Run**:
  - Use `docker-compose up --build` for the full stack.
  - Run backend and frontend separately for development.
- **Testing**:
  - Execute `python test_lighting_pipeline.py` for pipeline tests.
  - Use `python pipeline_integration_example.py` for integration tests.
- **Debugging**:
  - Check logs in the `logs/` folder.
  - Use health checks via `python backend/health_check_service.py`.

## Additional Notes
- **No Hardcoded Fixtures**: Always extract fixture/channel info dynamically.
- **Error Handling**: Agents log errors and preserve partial results.
- **Frontend**: Uses WebSocket for real-time updates and Tailwind CSS for styling.
- **Song Analysis**: Results are cached to optimize performance for large files.