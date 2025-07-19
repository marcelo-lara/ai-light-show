# Agent Architecture Documentation

## Overview

The LangGraph Lighting Pipeline has been refactored into individual, modular agents for better organization, testing, and maintainability.

## File Structure

```
backend/services/langgraph/
├── lighting_pipeline.py           # Main pipeline orchestration
├── agents/
│   ├── __init__.py                # Agent exports
│   ├── context_builder.py         # Agent 1: Musical context interpretation
│   ├── lighting_planner.py        # Agent 2: Lighting action planning
│   └── effect_translator.py       # Agent 3: DMX command translation
```

## Agent Classes

### ContextBuilderAgent
**File**: `agents/context_builder.py`
**Purpose**: Interprets musical segments into natural language context summaries
**Model**: Mixtral (configurable)

```python
from backend.services.langgraph.agents import ContextBuilderAgent

agent = ContextBuilderAgent(model="mixtral")
result = agent.run(pipeline_state)
```

### LightingPlannerAgent  
**File**: `agents/lighting_planner.py`
**Purpose**: Creates high-level lighting actions from context summaries
**Model**: Mixtral (configurable)

```python
from backend.services.langgraph.agents import LightingPlannerAgent

agent = LightingPlannerAgent(model="mixtral")
result = agent.run(pipeline_state)
```

### EffectTranslatorAgent
**File**: `agents/effect_translator.py`
**Purpose**: Translates lighting actions into specific DMX commands
**Model**: Command-R with Mixtral fallback (configurable)

```python
from backend.services.langgraph.agents import EffectTranslatorAgent

agent = EffectTranslatorAgent(model="command-r", fallback_model="mixtral")
result = agent.run(pipeline_state)
```

## Benefits of Modular Design

### 1. **Independent Testing**
Each agent can be tested individually:
```python
# Test only the context builder
context_agent = ContextBuilderAgent()
context_result = context_agent.run(test_state)

# Test only the lighting planner
planner_agent = LightingPlannerAgent()
planner_result = planner_agent.run(context_result)
```

### 2. **Flexible Configuration**
Different models can be used for each agent:
```python
# Use different models for different tasks
context_agent = ContextBuilderAgent(model="llama2")
planner_agent = LightingPlannerAgent(model="mixtral")
translator_agent = EffectTranslatorAgent(model="command-r")
```

### 3. **Easy Extension**
New agents can be added without modifying existing code:
```python
# Add a new agent for beat detection
class BeatDetectorAgent:
    def run(self, state: PipelineState) -> PipelineState:
        # Implementation here
        pass
```

### 4. **Better Error Isolation**
Issues in one agent don't affect others:
```python
try:
    result = context_agent.run(state)
except Exception as e:
    print(f"Context agent failed: {e}")
    # Continue with fallback or skip this agent
```

### 5. **Partial Pipeline Execution**
Start from any point in the pipeline:
```python
# Skip context building, start from planning
state_with_context = {
    "segment": segment_data,
    "context_summary": "Pre-generated context",
    "actions": [],
    "dmx": []
}

planner_result = planner_agent.run(state_with_context)
final_result = translator_agent.run(planner_result)
```

## Usage Examples

### Basic Agent Usage
```python
from backend.services.langgraph.agents import ContextBuilderAgent

# Create agent with custom model
agent = ContextBuilderAgent(model="mixtral")

# Prepare state
state = {
    "segment": {
        "name": "Chorus",
        "start": 30.0,
        "end": 45.0,
        "features": {"energy": 0.8, "tempo": 128}
    },
    "context_summary": "",
    "actions": [],
    "dmx": []
}

# Run agent
result = agent.run(state)
print(f"Context: {result['context_summary']}")
```

### Partial Pipeline
```python
from backend.services.langgraph.agents import LightingPlannerAgent, EffectTranslatorAgent

# Start from step 2 (lighting planning)
planner = LightingPlannerAgent()
translator = EffectTranslatorAgent()

# State with pre-filled context
state = {
    "segment": segment_data,
    "context_summary": "High energy drop section with heavy bass",
    "actions": [],
    "dmx": []
}

# Run remaining pipeline steps
planning_result = planner.run(state)
final_result = translator.run(planning_result)
```

### Custom Error Handling
```python
def robust_agent_execution(agent, state):
    try:
        return agent.run(state)
    except Exception as e:
        print(f"Agent {agent.__class__.__name__} failed: {e}")
        # Return state with error marker
        error_state = state.copy()
        error_state["error"] = str(e)
        return error_state

# Use with any agent
context_agent = ContextBuilderAgent()
result = robust_agent_execution(context_agent, initial_state)
```

## LangGraph Compatibility

All agents maintain compatibility with LangGraph through wrapper functions:

```python
# These functions are available for LangGraph workflows
from backend.services.langgraph.agents.context_builder import run_context_builder
from backend.services.langgraph.agents.lighting_planner import run_lighting_planner
from backend.services.langgraph.agents.effect_translator import run_effect_translator

# Used automatically in the main pipeline
workflow.add_node("context_builder", run_context_builder)
workflow.add_node("lighting_planner", run_lighting_planner)
workflow.add_node("effect_translator", run_effect_translator)
```

## Migration Notes

- **Old Code**: All agent logic was in `lighting_pipeline.py`
- **New Code**: Each agent is in its own file under `agents/`
- **Compatibility**: The main pipeline API remains unchanged
- **Testing**: New individual agent testing capabilities added

## Testing

Run individual agent tests:
```bash
python test_agents_individual.py
```

Run full pipeline tests:
```bash
python test_lighting_pipeline.py
```

Run integration tests:
```bash
python pipeline_integration_example.py
```
