
# Agent Architecture Documentation

## Overview

The AI Light Show backend uses modular, LLM-driven agents to analyze music and generate lighting actions. Each agent is implemented as a Python class in `backend/services/agents/`, with a clear separation of responsibilities and LLM-friendly interfaces. Agents are orchestrated in sequence (or independently) and can be composed using frameworks like LlamaIndex.
The prompts are created using Jinja2 templates located on the `backend/services/agents/prompts`

## File Structure

```
backend/services/agents/
├── lighting_planner.py        # LightingPlannerAgent: lighting action planning
└── effect_translator.py       # EffectTranslatorAgent: DMX command translation
```

## Agent Classes and LLM Instructions

### LightingPlannerAgent
**File**: `lighting_planner.py`

**Purpose**: Analyzes musical segments and generates concise, natural language context summaries for lighting design. 
The goal is to create a Lighting Plan.
e.g.
user: Create a plan for the intro
agent: ""
#plan add at 0.0 "Intro start" "half intensity blue chaser from left to right at 1b interbals."
#plan add at 15.0 "Intro build" "fade from blue to white from right to left every 1b interbals"
#plan add at 31.42 "Intro head" "center sweep the moving head pointing the piano"
""


### EffectTranslatorAgent
**File**: `effect_translator.py`
**Purpose**: Translate Ligthing plan entries into fixtures actions with precise times.
It is important to instruct the agent to:
- create ALL actions required to achieve the effect.

e.g.
user: Half intensity blue chaser from left to right at 1b interbals.
agent: ""
#fade parcan_pl blue at 0.2 intensity 0.5 for 0.32s
#fade parcan_l blue at 0.4 intensity 0.5 for 0.32s
#fade parcan_r blue at 0.6 intensity 0.5 for 0.32s
#fade parcan_pr blue at 0.8 intensity 0.5 for 0.32s
#fade parcan_pl blue at 1.0 intensity 0.5 for 0.32s
#fade parcan_l blue at 1.2 intensity 0.5 for 0.32s
#fade parcan_r blue at 1.4 intensity 0.5 for 0.32s
#fade parcan_pr blue at 1.6 intensity 0.5 for 0.32s
""

---
**For LLM developers:**
- All prompts should be explicit, concise, and focused on the agent's role.
- Always return explicit commands to be interpreted at the response.
- Use exact beat times retrieved from the /analyze endpoint from song_analysis (see song_analysis/README.md for details)
- All Agents must be child classes of AgentModel (`backend/services/agents/_agent_model.py`)