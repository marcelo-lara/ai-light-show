# LangGraph 3-Agent Lighting Pipeline

## Overview

The LangGraph Lighting Pipeline is a sophisticated 3-agent chain that transforms musical segment analysis into DMX lighting commands through AI reasoning:

**Context Builder** → **Lighting Planner** → **Effect Translator**

## Architecture

### Agent 1: Context Builder (Mixtral)
- **Input**: Raw segment data with musical features
- **Output**: Natural language context summary
- **Purpose**: Interprets the emotional and sonic character of the music
- **Example**: "High energy climax with heavy bass and bright synth leads"

### Agent 2: Lighting Planner (Mixtral) 
- **Input**: Context summary + segment features
- **Output**: High-level lighting actions and cues
- **Purpose**: Translates musical context into lighting design concepts
- **Example**: ["strobe_white", "chase_red_blue", "dim_ambient"]

### Agent 3: Effect Translator (Command-R)
- **Input**: Lighting actions + fixture definitions
- **Output**: Specific DMX commands with channel values
- **Purpose**: Converts abstract lighting concepts into concrete DMX instructions
- **Example**: [{"channel": 1, "value": 255}, {"channel": 4, "value": 128}]

## Features

### LangGraph Integration
- Uses LangGraph's StateGraph for robust workflow orchestration
- TypedDict state management for type safety
- Automatic error recovery and fallback

### Fallback Mode
- When LangGraph is unavailable, runs in sequential mode
- Maintains all functionality without external dependencies
- Graceful degradation for production environments

### Comprehensive Logging
- Each node output saved to `logs/{node_name}.json`
- Complete pipeline results logged for debugging
- Error states captured for analysis

### Error Handling
- Each agent handles failures gracefully
- Pipeline continues even if individual nodes fail
- Partial results preserved for downstream processing

## Usage

### Basic Usage
```python
from backend.services.langgraph.lighting_pipeline import run_lighting_pipeline

# Prepare segment input
segment_input = {
    "segment": {
        "name": "Chorus",
        "start": 24.0,
        "end": 40.0,
        "features": {
            "energy": 0.9,
            "valence": 0.8,
            "tempo": 120,
            "key": "C",
            "loudness": -5.0,
            "danceability": 0.9
        }
    }
}

# Run the pipeline
result = run_lighting_pipeline(segment_input)

# Access results
context = result["context_summary"]
actions = result["actions"]
dmx_commands = result["dmx"]
```

### FastAPI Integration
```python
@router.post("/generate-lighting-design")
async def generate_lighting_design(song_analysis: dict):
    segments = song_analysis.get('segments', [])
    lighting_results = []
    
    for segment in segments:
        segment_input = {
            "segment": {
                "name": segment.get('label', 'Unknown'),
                "start": segment.get('start', 0.0),
                "end": segment.get('end', 0.0),
                "features": segment.get('features', {})
            }
        }
        
        result = run_lighting_pipeline(segment_input)
        lighting_results.append(result)
    
    return {"lighting_design": lighting_results}
```

## State Schema

The pipeline uses a TypedDict for type-safe state management:

```python
class PipelineState(TypedDict):
    segment: Dict[str, Any]      # Musical segment data
    context_summary: str         # Agent 1 output
    actions: list               # Agent 2 output  
    dmx: list                   # Agent 3 output
```

## Configuration

### Model Selection
- **Context Builder**: Mixtral (creative interpretation)
- **Lighting Planner**: Mixtral (strategic planning)
- **Effect Translator**: Command-R (precise technical output)

### Ollama Connection
- Default endpoint: `http://llm-server:11434`
- Configurable via environment variables
- Automatic fallback on connection errors

## Output Format

### Context Summary
Natural language description of the musical segment's character and mood.

### Lighting Actions
Array of high-level lighting concepts and cues:
```json
[
  "strobe_white_fast",
  "chase_red_blue_diagonal", 
  "dim_ambient_to_30",
  "pulse_bass_sync"
]
```

### DMX Commands
Specific channel values for lighting fixtures:
```json
[
  {"channel": 1, "value": 255, "fixture": "spot_1"},
  {"channel": 4, "value": 128, "fixture": "wash_2"},
  {"channel": 7, "value": 0, "fixture": "strobe_1"}
]
```

## Logging and Debugging

### Node Outputs
Each agent's output is automatically saved:
- `logs/context_builder.json`
- `logs/lighting_planner.json` 
- `logs/effect_translator.json`
- `logs/pipeline_complete.json`

### Error Diagnostics
- Connection errors logged with full stack traces
- Partial results preserved for analysis
- Pipeline continues with graceful degradation

## Testing

Run the test suite:
```bash
python test_lighting_pipeline.py
```

Run integration example:
```bash
python pipeline_integration_example.py
```

## Dependencies

### Required
- `typing_extensions` (TypedDict support)
- `ollama` (LLM API client)
- `pathlib` (file operations)

### Optional
- `langgraph` (enhanced workflow orchestration)
- Falls back to sequential mode if unavailable

## Performance

- **Latency**: ~2-5 seconds per segment (depends on LLM response time)
- **Throughput**: Can process multiple segments in parallel
- **Memory**: Low footprint, state cleaned between segments
- **Reliability**: Robust error handling, graceful degradation

## Extensibility

### Adding New Agents
1. Create new node function with `PipelineState` signature
2. Add to LangGraph workflow with `add_node()`
3. Connect with edges using `add_edge()`
4. Update state schema if needed

### Custom Models
- Modify model selection in each node function
- Update prompts for different model capabilities
- Configure endpoints for different providers

### Enhanced Features
- Implement conditional routing based on segment features
- Add parallel processing for complex scenes
- Integrate with real-time beat detection
- Support for multiple fixture types and protocols
