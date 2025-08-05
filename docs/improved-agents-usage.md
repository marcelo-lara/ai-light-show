# Improved AI Light Show Agents

This document describes the enhanced `LightingPlannerAgent` and `EffectTranslatorAgent` implementations optimized for Ollama and ChatGPT-like UI experiences.

## Key Improvements

### 🚀 Performance Optimizations
- **Async/await support** for non-blocking operations
- **Streaming callbacks** for real-time UI updates
- **Batch processing** in EffectTranslatorAgent for efficiency
- **Intelligent caching** of beat times and song data
- **Reduced context size** with smart templating

### 🎯 Ollama Best Practices
- **Temperature control** for consistent results
- **Structured JSON output** where appropriate
- **Clear, focused prompts** with examples
- **Error handling** with graceful fallbacks
- **Model-agnostic design** supporting multiple LLMs

### 💬 ChatGPT-like UI Features
- **Real-time streaming** responses
- **Progress indicators** during processing
- **Contextual error messages**
- **Convenience methods** for common operations
- **State management** for conversation flow

## Usage Examples

### Basic Usage (Async - Recommended)

```python
import asyncio
from backend.services.agents.lighting_planner import LightingPlannerAgent
from backend.services.agents.effect_translator import EffectTranslatorAgent

async def create_lighting_show():
    # Initialize agents
    planner = LightingPlannerAgent(model_name="mixtral")
    translator = EffectTranslatorAgent(model_name="mixtral")
    
    # Streaming callback for UI updates
    def on_stream(chunk: str):
        print(f"AI: {chunk}", end="", flush=True)
    
    # Create lighting plan
    plan_result = await planner.run_async({
        "user_prompt": "Create an energetic intro with blue lights and moving heads",
        "context_summary": "Electronic dance music, BPM: 128"
    }, callback=on_stream)
    
    # Translate to actions
    action_result = await translator.run_async({
        "lighting_plan": plan_result["lighting_plan"]
    }, callback=on_stream)
    
    return action_result["actions"]

# Run
actions = asyncio.run(create_lighting_show())
```

### Convenience Methods

```python
async def quick_lighting_plan():
    planner = LightingPlannerAgent()
    
    # Quick user prompt
    result = await planner.create_plan_from_user_prompt_async(
        "Make the lights pulse with the beat",
        callback=lambda chunk: ui.update_streaming_text(chunk)
    )
    
    # Quick single effect
    translator = EffectTranslatorAgent()
    actions = await translator.translate_single_effect(
        "strobe all lights red",
        time=30.5,
        duration=4.0
    )
    
    return result, actions
```

### Synchronous Usage (Fallback)

```python
def simple_sync_usage():
    planner = LightingPlannerAgent()
    
    result = planner.run({
        "user_prompt": "Create intro lighting",
        "context_summary": "Pop song, 120 BPM"
    })
    
    return result["lighting_plan"]
```

## Agent Architecture

### LightingPlannerAgent

**Purpose**: Creates high-level lighting plans with natural language descriptions and precise timing.

**Key Features**:
- Automatic beat time fetching from song analysis
- Smart context building from app_state
- Streaming response support
- Multiple convenience methods for different use cases

**Output Format**:
```python
{
    "lighting_plan": [
        {
            "time": 0.487,
            "label": "Intro start", 
            "description": "half intensity blue chaser from left to right"
        }
    ],
    "exact_beats": [0.487, 0.893, 1.302, ...],
    "status": "success"
}
```

### EffectTranslatorAgent

**Purpose**: Converts lighting plan descriptions into executable DMX actions.

**Key Features**:
- Batch processing for efficiency
- Precise timing alignment with beat data
- Fixture-aware action generation
- JSON output parsing with validation

**Output Format**:
```python
{
    "actions": [
        "fade parcan_pl blue at 0.487 intensity 0.5 for 0.4s",
        "fade parcan_l blue at 0.893 intensity 0.5 for 0.4s"
    ],
    "translated_count": 1,
    "status": "success"
}
```

## UI Integration Patterns

### Real-time Streaming

```python
class LightingUI:
    async def handle_user_prompt(self, prompt: str):
        self.show_thinking_indicator()
        
        planner = LightingPlannerAgent()
        
        def on_stream(chunk):
            self.update_ai_response(chunk)
        
        result = await planner.create_plan_from_user_prompt_async(
            prompt, 
            callback=on_stream
        )
        
        self.hide_thinking_indicator()
        self.show_final_result(result)
```

### Progress Tracking

```python
async def track_progress(agent, input_data):
    # Start agent
    task = asyncio.create_task(agent.run_async(input_data))
    
    # Monitor progress
    while not task.done():
        progress = agent.state.progress
        status = agent.state.status
        ui.update_progress(progress, status)
        await asyncio.sleep(0.1)
    
    return await task
```

### Error Handling

```python
async def robust_agent_call():
    try:
        result = await agent.run_async(data, callback=stream_callback)
        
        if result["status"] == "error":
            ui.show_error(f"AI Error: {result['error']}")
            return None
            
        return result
        
    except ConnectionError:
        ui.show_error("Cannot connect to AI service. Please check Ollama is running.")
    except Exception as e:
        ui.show_error(f"Unexpected error: {str(e)}")
        logger.exception("Agent call failed")
```

## Performance Tips

### 1. Use Async Methods
```python
# ✅ Good - Non-blocking
result = await agent.run_async(data, callback=ui_update)

# ❌ Avoid - Blocks UI thread
result = agent.run(data)
```

### 2. Implement Streaming
```python
# ✅ Good - Real-time feedback
def stream_callback(chunk):
    ui.append_text(chunk)
    ui.scroll_to_bottom()

result = await agent.run_async(data, callback=stream_callback)
```

### 3. Cache Heavy Operations
```python
# Agent automatically caches beat times, but you can help:
if not hasattr(self, '_cached_beats'):
    self._cached_beats = await fetch_beat_times()
```

### 4. Use Appropriate Models
```python
# For quick responses
quick_agent = LightingPlannerAgent(model_name="mistral")

# For complex tasks
detailed_agent = LightingPlannerAgent(model_name="mixtral")
```

## Configuration

### Model Selection
- **mistral**: Fast, good for simple tasks
- **mixtral**: Better reasoning, complex tasks
- **llama3**: Good balance of speed and quality

### Temperature Settings
```python
# More creative (default: 0.7)
agent._call_ollama_async(prompt, temperature=0.9)

# More consistent
agent._call_ollama_async(prompt, temperature=0.3)
```

## Testing

Run the test suite:
```bash
python test_improved_agents.py
```

The tests cover:
- Async/sync functionality
- Streaming callbacks
- Error handling
- Convenience methods
- Performance under load

## Best Practices Summary

1. **Always use async methods** in UI applications
2. **Implement streaming callbacks** for real-time feedback
3. **Handle errors gracefully** with user-friendly messages
4. **Use appropriate models** for the task complexity
5. **Cache expensive operations** like beat analysis
6. **Provide progress indicators** for long-running tasks
7. **Test error scenarios** thoroughly
8. **Monitor agent state** for debugging

This implementation provides a solid foundation for a ChatGPT-like AI lighting system with excellent performance and user experience.
