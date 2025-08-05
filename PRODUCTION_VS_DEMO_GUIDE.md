# Production vs Demo AI Lighting Assistant Guide

## Overview

We have two versions of the AI Lighting Assistant:

1. **`ai_lighting_assistant.py`** - Demo version with mock agents and comprehensive logging
2. **`ai_lighting_assistant_production.py`** - Production version with real agent integration

## Key Differences

### Demo Version (`ai_lighting_assistant.py`)
- **Purpose**: Testing, debugging, and demonstration of logging
- **Agents**: Mock agents (`None`) for testing without dependencies
- **Logging**: Comprehensive logging for all operations and debug information
- **Use Case**: When you want to test the assistant logic without running real agents

```python
# Demo version - mock agents
self.planner = None  # Mock LightingPlannerAgent
self.translator = None  # Mock EffectTranslatorAgent

# Mock responses for testing
async def _mock_planner_response(self, user_prompt: str, context: str, callback):
    return {
        "status": "success",
        "lighting_plan": [
            {"time": 0.0, "label": "Mock Entry", "description": "Test plan entry"}
        ]
    }
```

### Production Version (`ai_lighting_assistant_production.py`)
- **Purpose**: Real deployment with actual agent integration
- **Agents**: Real agent instances with full functionality
- **Logging**: Comprehensive logging for production monitoring
- **Use Case**: When you want to run the assistant with actual LLM agents

```python
# Production version - real agents
self.planner = LightingPlannerAgent(model_name=model_name)
self.translator = EffectTranslatorAgent(model_name=model_name)

# Real agent calls
plan_result = await self.planner.create_plan_from_user_prompt_async(
    user_prompt=message,
    context_summary=context,
    callback=callback
)
```

## Logging Features (Both Versions)

### Comprehensive Request Tracking
```
💬 Processing user message: Create energetic intro lighting
🎯 Routing to planning request handler
🤖 Calling LightingPlannerAgent.create_plan_from_user_prompt_async
📊 LightingPlannerAgent result: status=success
✅ Generated 5 lighting plan entries
🤖 Calling EffectTranslatorAgent.run_async
📊 EffectTranslatorAgent result: status=success
✅ Generated 12 fixture actions
✅ Planning request completed successfully
```

### Sub-Agent Call Logging
- **Request routing**: Logs which handler (planning, direct action, general) is used
- **Agent inputs**: Logs prompts, context, and parameters sent to sub-agents
- **Agent outputs**: Logs results, status, and action counts from sub-agents
- **Error handling**: Logs exceptions with full stack traces
- **Performance**: Logs timing and success/failure status

### Debug Information
- **Intent detection**: Logs keyword matches for routing decisions
- **Context building**: Logs song metadata and app state used
- **Action generation**: Logs fixture actions and lighting plans
- **Conversation history**: Tracks user/assistant message flow

## Usage Examples

### Demo Version Testing
```python
# Test the logic without real agents
python ai_lighting_assistant.py
```

### Production Usage
```python
from ai_lighting_assistant_production import ProductionAILightingAssistant

# Initialize with real agents
assistant = ProductionAILightingAssistant(model_name="mixtral")

# Process real requests
result = await assistant.chat("Create energetic intro lighting")
```

### WebSocket Integration
```python
# Use in WebSocket handlers
from ai_lighting_assistant_production import websocket_chat_handler

# In your WebSocket route
await websocket_chat_handler(websocket, {"text": user_message})
```

## Logging Configuration

### Development Logging
```python
# Enable debug logging for development
logging.getLogger('ai_lighting_assistant').setLevel(logging.DEBUG)
```

### Production Logging Setup
```python
from ai_lighting_assistant_production import setup_production_logging

# Comprehensive logging with rotation
setup_production_logging()
```

This creates:
- Console output for immediate feedback
- `logs/ai_lighting_assistant.log` for general logging
- `logs/ai_lighting_assistant_detailed.log` with rotation (10MB files, 5 backups)

## Log Analysis

### Finding Sub-Agent Issues
```bash
# Search for agent call failures
grep "❌.*Agent" logs/ai_lighting_assistant.log

# Track specific agent calls
grep "🤖 Calling" logs/ai_lighting_assistant_detailed.log
```

### Performance Monitoring
```bash
# Find slow operations
grep "Planning request completed" logs/ai_lighting_assistant.log

# Check routing decisions
grep "🎯 Routing" logs/ai_lighting_assistant.log
```

### Error Investigation
```bash
# Get full error context
grep -A 10 -B 5 "❌" logs/ai_lighting_assistant_detailed.log
```

## Migration Path

### From Demo to Production

1. **Test with demo version**:
   ```bash
   python ai_lighting_assistant.py
   ```

2. **Verify agent implementations**:
   - Ensure `LightingPlannerAgent` is fully implemented
   - Ensure `EffectTranslatorAgent` is fully implemented
   - Test agents individually

3. **Switch to production version**:
   ```python
   from ai_lighting_assistant_production import ProductionAILightingAssistant
   ```

4. **Monitor logs**:
   - Check for real agent call successes/failures
   - Verify LLM responses are appropriate
   - Monitor performance and error rates

## Best Practices

### Development
- Use demo version for testing new features
- Verify logging before implementing in production
- Test error handling with mock failures

### Production
- Use production version with real agents
- Monitor logs for performance issues
- Set up log rotation and archival
- Alert on error patterns

### Debugging
- Use debug logging level during development
- Filter logs by emoji prefixes for specific operations
- Track conversation history for context

## Next Steps

1. **Integration Testing**: Test production version with real agents end-to-end
2. **Performance Tuning**: Monitor and optimize agent call performance
3. **Error Handling**: Add more specific error recovery for different failure modes
4. **Monitoring**: Set up automated monitoring and alerting for production logs
