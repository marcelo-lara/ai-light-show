# Improved UI Agent - Intelligent Router

The UI Agent has been completely redesigned as an intelligent router that uses LLM-powered intent analysis to determine the best way to handle user requests. This eliminates hardcoded routing logic and provides a more flexible, ChatGPT-like experience.

## 🧠 Core Architecture

### Intelligent Routing Process

1. **Intent Analysis** - LLM analyzes user request and determines routing strategy
2. **Route Selection** - Based on analysis, routes to appropriate handler:
   - `direct_command` - Immediate lighting actions
   - `lighting_plan` - Structured lighting sequences  
   - `effect_translation` - Convert effects to fixture actions
   - `conversation` - General questions and help

3. **Specialized Processing** - Each route uses the appropriate agent or handler
4. **Response Generation** - Provides contextual, helpful responses

### No Hardcoded Logic

❌ **Old Approach**: Hardcoded keyword matching
```python
if "flash" in user_input:
    return execute_flash()
elif "plan" in user_input:
    return create_plan()
```

✅ **New Approach**: LLM-powered intent analysis
```python
routing_decision = await self._analyze_user_intent(user_prompt)
# LLM decides based on context, not keywords
```

## 🎯 Routing Categories

### 1. Direct Commands
**When**: User wants immediate lighting actions
**Examples**: 
- "Flash all lights red"
- "Strobe the moving heads"
- "Fade to blue"
- "Clear all actions"

**Handler**: `_handle_direct_command()` → DirectCommandsParser

### 2. Lighting Plan
**When**: User wants structured lighting sequences
**Examples**:
- "Create intro lighting"
- "Plan the chorus section" 
- "Design lights for the whole song"

**Handler**: `_handle_lighting_plan_request()` → LightingPlannerAgent

### 3. Effect Translation
**When**: User wants to convert effects to actions
**Examples**:
- "Translate this blue strobe effect"
- "Make this work with moving heads"
- "Convert to parcan actions"

**Handler**: `_handle_effect_translation_request()` → EffectTranslatorAgent

### 4. Conversation
**When**: General questions, help, unclear requests
**Examples**:
- "What can you help me with?"
- "How do strobing effects work?"
- "What fixtures are available?"

**Handler**: `_handle_conversational_request()` → Conversational template

## 💬 Usage Examples

### Basic Chat Interface
```python
async def chat_with_ai():
    ui_agent = UIAgent()
    
    def stream_callback(chunk):
        chat_ui.append_text(chunk)
    
    # User sends message
    result = await ui_agent.run({
        "prompt": "Create energetic intro lighting",
        "callback": stream_callback
    })
    
    print(f"Response: {result['response']}")
    print(f"Routing: {result['routing']['type']}")
```

### Conversation History
```python
ui_agent = UIAgent()

# Add messages to history
ui_agent.add_to_conversation("user", "What can you do?")
ui_agent.add_to_conversation("assistant", "I can help with lighting control...")

# Get history
history = ui_agent.get_conversation_history()

# Clear when needed
ui_agent.clear_conversation_history()
```

### Quick Responses
```python
# For simple interactions
response = await ui_agent.quick_response(
    "What fixtures are available?",
    callback=ui_update
)
```

## 🎛️ Integration with Specialized Agents

### Automatic Agent Coordination
The UI Agent automatically coordinates with specialized agents:

```python
# User: "Plan lighting for the intro"
# → Routes to LightingPlannerAgent
# → Returns structured plan

# User: "Translate that plan to actions"  
# → Routes to EffectTranslatorAgent
# → Converts plan to executable actions

# User: "Execute those actions now"
# → Routes to DirectCommandsParser
# → Executes actions immediately
```

### Streaming Support
All routes support real-time streaming:

```python
async def handle_user_message(message):
    def on_stream(chunk):
        websocket.send({"type": "ai_chunk", "data": chunk})
    
    result = await ui_agent.run({
        "prompt": message,
        "callback": on_stream
    })
    
    # Final result
    websocket.send({"type": "ai_complete", "data": result})
```

## 🔄 Response Flow Examples

### Planning Request Flow
```
👤 User: "Create lighting for an energetic chorus"
🧠 Intent Analysis: lighting_plan (confidence: 0.9)
🎛️ Route to: LightingPlannerAgent
📝 LLM Response: "I'll create an energetic lighting plan..."
✅ Result: Structured lighting plan with beat-synced entries
```

### Direct Action Flow  
```
👤 User: "Flash all lights red now"
🧠 Intent Analysis: direct_command (confidence: 0.95)
⚡ Route to: DirectCommandsParser  
🎭 Execute: "#action flash all red at 0 for 2s"
✅ Result: Immediate lighting action executed
```

### Conversational Flow
```
👤 User: "What can you help me with?"
🧠 Intent Analysis: conversation (confidence: 0.8)
💬 Route to: Conversational handler
🤖 LLM Response: "I can help you create amazing lighting effects..."
✅ Result: Helpful, contextual information
```

## 🛡️ Error Handling & Robustness

### Graceful Degradation
```python
# If routing fails, defaults to conversation
if routing_decision["type"] == "unknown":
    routing_decision = {"type": "conversation"}

# If specialized agent fails, provides helpful error
if agent_result["status"] == "error":
    return friendly_error_message(agent_result["error"])
```

### Input Validation
- Empty prompts are caught and handled
- Overly long prompts are managed appropriately
- Special characters are processed safely
- Invalid fixture references are corrected

### Connection Resilience
- Handles Ollama service unavailable
- Graceful fallbacks for model errors
- Timeout management for long operations

## 📊 Performance Optimizations

### Concurrent Processing
- Multiple requests can be processed simultaneously
- Streaming responses provide immediate feedback
- Specialized agents run in parallel when possible

### Efficient Context Management
- Smart context building reduces prompt size
- Caches song and fixture information
- Reuses conversation history efficiently

### Memory Management
- Conversation history has configurable limits
- Old entries are cleaned up automatically
- Large responses are chunked appropriately

## 🎨 ChatGPT-like Features

### Natural Conversation
- Maintains context across multiple exchanges
- Remembers previous requests and responses
- Provides follow-up suggestions and guidance

### Real-time Feedback
- Streaming responses for immediate engagement
- Progress indicators during processing
- Status updates for long operations

### Intelligent Suggestions
- Suggests next steps based on current context
- Provides examples and guidance
- Offers alternative approaches

### Contextual Help
- Understands current song and fixture state
- Provides relevant suggestions
- Explains system capabilities clearly

## 🔧 Configuration Options

### Model Selection
```python
# Fast responses
ui_agent = UIAgent(model_name="mistral")

# Better reasoning  
ui_agent = UIAgent(model_name="mixtral")

# Balanced performance
ui_agent = UIAgent(model_name="gemma3n:e4b")
```

### Debug Mode
```python
# Enable detailed logging
ui_agent = UIAgent(debug=True)
```

### Conversation Management
```python
# Set history limits
ui_agent.conversation_history_limit = 20

# Auto-clear after inactivity
ui_agent.auto_clear_after = 3600  # 1 hour
```

## 🚀 Benefits

1. **Intelligent Routing** - LLM makes smart decisions about request handling
2. **No Hardcoded Logic** - Flexible, adaptable to new request types
3. **ChatGPT-like Experience** - Natural conversation with context awareness
4. **High Performance** - Async processing with streaming support
5. **Robust Error Handling** - Graceful degradation and helpful error messages
6. **Easy Integration** - Simple API for web interfaces and chat systems

The improved UI Agent provides a foundation for creating sophisticated, conversational lighting control interfaces that feel natural and intelligent while maintaining the precision and reliability needed for professional DMX lighting control.
