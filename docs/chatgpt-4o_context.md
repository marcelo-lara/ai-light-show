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
- **Purpose**: Defines lighting fixture configurations and spatial positioning.
- **Key Files**:
  - `fixtures.json`: JSON file containing fixture definitions with channel mappings, effects, and position data.

#### Fixture Configuration Structure
Each fixture in `fixtures.json` includes:
- **Basic Info**: `id`, `name`, `type` (e.g., "moving_head", "rgb")
- **DMX Channels**: Channel mappings (e.g., `"dim": 16, "red": 17`)
- **Effects**: Available effects (e.g., "strobe", "flash", "fade")
- **Position**: 3D coordinates and labels (e.g., `{"x": 0.5, "y": 0.05, "z": 0.9, "label": "center_stage"}`)
- **Presets**: Named configurations for quick recall
- **Metadata**: Channel types, value mappings, and constraints

#### Fixture Model (`backend/models/fixtures/fixture_model.py`)
- **Properties**:
  - `position`: Returns a `Position` dataclass with x, y, z coordinates and label
  - `channel_names`: DMX channel mapping from configuration
  - `actions`: Available actions derived from action handlers
- **Methods**:
  - `render_action()`: Execute lighting effects
  - `set_arm()`: Enable/disable fixture channels
  - `set_channel_value()`: Set specific channel values
  - `fade_channel()`: Create smooth transitions between values

#### Fixtures List Model (`backend/models/fixtures/fixtures_list_model.py`)
- **Position-Based Queries**:
  - `get_fixtures_by_position_label()`: Find fixtures by position label (e.g., "stage_left")
  - `get_fixtures_in_area()`: Find fixtures within a rectangular area using x,y coordinates
- **Automatic Position Loading**: Position data is automatically loaded from `fixtures.json` when fixtures are initialized
- **Debug Output**: Shows fixture positions when debug mode is enabled

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

## Key Data Models

### Position Dataclass (`backend/models/position.py`)
- **Purpose**: Represents 3D spatial coordinates for fixtures
- **Fields**:
  - `x`: Float representing horizontal position (0.0-1.0 normalized)
  - `y`: Float representing vertical position (0.0-1.0 normalized) 
  - `z`: Optional float for depth/height
  - `label`: Optional string identifier (e.g., "center_stage", "stage_left")

### Fixture Model Architecture
- **Base Class**: `FixtureModel` provides common functionality
- **Specialized Classes**: Type-specific implementations (e.g., RGB, Moving Head)
- **DMX Canvas Integration**: All fixtures use a singleton DMX canvas for rendering
- **Dynamic Configuration**: Fixture capabilities loaded from `fixtures.json`

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