
# Agent Architecture Documentation

## Overview

The AI Light Show backend uses modular, LLM-driven agents to analyze music and generate lighting actions. Each agent is implemented as a Python class in `backend/services/agents/`, with a clear separation of responsibilities and LLM-friendly interfaces. Agents are orchestrated in sequence (or independently) and can be composed using frameworks like LlamaIndex.

## File Structure

```
backend/services/agents/
├── __init__.py                # Agent exports
├── context_builder.py         # ContextBuilderAgent: musical context interpretation
├── lighting_planner.py        # LightingPlannerAgent: lighting action planning
└── effect_translator.py       # EffectTranslatorAgent: DMX command translation
```

## Agent Classes and LLM Instructions

### ContextBuilderAgent
**File**: `context_builder.py`

**Purpose**: Analyzes musical segments and generates concise, natural language context summaries for lighting design. Optionally, can process an entire song in chunks and assemble a timeline of lighting actions.

**LLM Prompt Pattern:**
```
You are a music context interpreter.
Describe the emotional and sonic feel of this section:

Segment: {name}
Start: {start_time}s
End: {end_time}s
Features: {features_json}

Respond with a short natural language summary like:
"High energy climax with heavy bass and bright synth"

Focus on the mood, energy level, and key instruments. Keep it concise and descriptive.
```

**Key Methods:**
- `run(state: PipelineState) -> PipelineState`: Given a segment dict, returns a state with a context summary (calls LLM via `query_ollama`).
- `extract_lighting_actions(response: str, start_time: float, end_time: float) -> list`: Parses LLM output for lighting actions, with fallback to generic action if no structured data is found.
- `analyze_song_context(...)`: Asynchronously analyzes an entire song, chunk by chunk, updating progress and saving partial results. Uses the global `app_state` for state and progress tracking.

**LLM-Friendly Context:**
- All prompts are explicit, concise, and focused on musical mood and features.
- LLM responses are expected to be short summaries or structured JSON (for lighting actions).
- Error handling and progress reporting are built-in for robust orchestration.

### LightingPlannerAgent
**File**: `lighting_planner.py`

**Purpose**: Converts context summaries into high-level lighting actions (e.g., strobe, color changes, movement cues). Uses LLMs to interpret context and generate a list of lighting actions for each segment.

**LLM Prompt Pattern:**
```
You are a lighting designer. Given the following musical context, generate a list of lighting actions (as JSON) that would best express the mood and energy of the segment.

Context: {context_summary}
Segment: {segment_info}

Respond with a JSON list of lighting actions, each with start, end, type, color, intensity, and description fields.
```

**Key Methods:**
- `run(state: PipelineState) -> PipelineState`: Given a state with context summary, returns a state with lighting actions (calls LLM).
- LLM output is parsed for a list of lighting actions; fallback to generic action if needed.

**LLM-Friendly Context:**
- Prompts are structured to elicit JSON lists of actions.
- All lighting actions are described in terms of time, type, color, intensity, and description.

### EffectTranslatorAgent
**File**: `effect_translator.py`

**Purpose**: Translates high-level lighting actions into concrete DMX channel commands, suitable for real hardware. Uses LLMs to map abstract actions to DMX values and timings.

**LLM Prompt Pattern:**
```
You are a DMX effect translator. Given a list of lighting actions, output the corresponding DMX channel commands (as JSON) for each action.

Actions: {actions_json}
Fixture definitions: {fixtures_json}

Respond with a JSON list of DMX commands, each with channel, value, start, end, and description fields.
```

**Key Methods:**
- `run(state: PipelineState) -> PipelineState`: Given a state with lighting actions, returns a state with DMX commands (calls LLM).
- LLM output is parsed for DMX command lists; fallback to generic DMX action if needed.

**LLM-Friendly Context:**
- Prompts include fixture definitions and expect structured JSON output.
- All DMX commands are described in terms of channel, value, timing, and description.

## Agent Orchestration

- Agents are designed to be composed in sequence: ContextBuilderAgent → LightingPlannerAgent → EffectTranslatorAgent.
- Each agent operates on a shared `PipelineState` dict, passing results to the next agent.
- Agents can be run independently for testing or partial pipeline execution.
- Orchestration is framework-agnostic (e.g., can be used with LlamaIndex, custom scripts, or other workflow tools).

## Testing and Debugging

- Each agent can be tested individually by calling its `run()` method with a suitable state dict.
- For full song analysis, use `ContextBuilderAgent.analyze_song_context()` (async, with progress reporting).
- All agent outputs can be logged to the `logs/` directory for inspection.
- Use the provided test scripts (e.g., `python test_lighting_pipeline.py`) for end-to-end validation.

## Migration Notes

- All agent logic is now modularized in `backend/services/agents/`.
- No hardcoded logic: all user prompts and musical analysis are handled by LLMs.
- Global state and fixtures are managed via `app_state` and `fixtures.json`.
- No references to LangGraph remain; orchestration is now open to LlamaIndex or other frameworks.

---
**For LLM developers:**
- All prompts should be explicit, concise, and focused on the agent's role.
- Always return structured JSON when requested.
- Avoid hardcoded or static responses; use the provided context and features.
