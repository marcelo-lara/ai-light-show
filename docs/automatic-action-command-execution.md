# Automatic Action Command Execution from Ollama Responses

## Overview

The AI light show system now automatically detects and executes action commands that appear in Ollama's streaming responses. When the AI model includes commands like `#add flash to parcan_l at 5.2s` in its response, these commands are automatically parsed and executed in real-time as the response streams.

## How It Works

### 1. Streaming Integration

The functionality is integrated into the `ollama_streaming.py` module:

- **Detection**: As chunks arrive from the Ollama streaming API, they are accumulated in a buffer
- **Pattern Matching**: Regular expressions scan the accumulated text for action command patterns
- **Validation**: Detected commands are validated against known command patterns
- **Execution**: Valid commands are executed using the existing `DirectCommandsParser`
- **Notification**: Results are sent back to the client via WebSocket

### 2. Command Detection Patterns

The system uses two regex patterns to capture different types of commands:

#### Simple Commands
```regex
#(?:action\s+)?(help|render|tasks|analyze(?:\s+context(?:\s+reset)?)?|clear\s+(?:all|id\s+\w+|group\s+\w+))
```

Captures: `#help`, `#render`, `#tasks`, `#analyze context`, `#clear all`, etc.

#### Complex Commands
```regex
#(?:action\s+)?((?:add|flash|fade|strobe|set|preset)\s+[^#\n]*?(?:at|to)\s+[\d.]+[sb]?[^#\n]*?)(?=\s*(?:\n|$|\.|\!|\?|,|\s+#|\s+[A-Z][a-z]))
```

Captures: `#add flash to parcan_l at 5.2s duration 1.5s`, `#flash all_parcans blue at 10s`, etc.

### 3. Command Validation

Detected commands are validated using predefined patterns:

```python
valid_patterns = [
    r'^help$',
    r'^render$',
    r'^tasks$',
    r'^analyze\s*(context\s*(reset)?)?$',
    r'^clear\s+(all|id\s+\w+|group\s+\w+)',
    r'^add\s+\w+\s+to\s+\w+\s+at\s+[\d.]+[sb]?(\s+(for|duration)\s+[\d.]+[sb]?)?',
    r'^(flash|fade|strobe|set|preset)\s+\w+.*?at\s+[\d.]+[sb]?',
    r'^(flash|fade|strobe)\s+\w+.*?(for|duration)\s+[\d.]+[sb]?',
    r'^(flash|fade|strobe)\s+\w+.*?with\s+intensity\s+[\d.]+',
]
```

### 4. Duplicate Prevention

- Commands are tracked in a set to prevent duplicate execution
- Same command text won't be executed multiple times within a single response

## Configuration

### Enabling/Disabling

Auto-execution can be controlled via parameters:

```python
current_response = await query_ollama_streaming(
    prompt, 
    session_id, 
    websocket=websocket,              # Required for execution
    auto_execute_commands=True        # Enable/disable auto-execution
)
```

### Requirements

- WebSocket connection must be provided for command execution
- DirectCommandsParser must be available
- App state (fixtures, song, etc.) must be properly initialized

## WebSocket Messages

When commands are executed, the client receives notifications:

### Success
```json
{
    "type": "actionCommandExecuted",
    "command": "#add flash to parcan_l at 5.2s duration 1.5s",
    "success": true,
    "message": "Added flash to parcan_l at 5.20s for 1.50s.",
    "data": {
        "universe": [...],
        "message": "DMX Canvas updated by direct command"
    }
}
```

### Error
```json
{
    "type": "actionCommandExecuted",
    "command": "#invalid command",
    "success": false,
    "message": "Error message describing what went wrong"
}
```

## Frontend Integration

The frontend handles these messages in `app.jsx`:

```javascript
case "actionCommandExecuted": {
    console.log("Action command executed:", msg);
    if (msg.success) {
        setToast(`🎭 Executed: ${msg.command}`);
        // Refresh DMX universe if provided
        if (msg.data && msg.data.universe) {
            onDmxUpdate(msg.data.universe);
        }
    } else {
        setToast(`❌ Failed: ${msg.command} - ${msg.message}`);
    }
    break;
}
```

## Examples

### AI Response with Commands

**AI Response:**
```
I'll create a lighting effect for you. Let me start with a flash on the left parcan:

#add flash to parcan_l at 5.2s duration 1.5s

Then I'll add a strobe effect:

#add strobe to moving_head at 10s duration 2s

Finally, let me render the result:

#render
```

**Execution Flow:**
1. `#add flash to parcan_l at 5.2s duration 1.5s` → Detected and executed
2. `#add strobe to moving_head at 10s duration 2s` → Detected and executed  
3. `#render` → Detected and executed

### Supported Command Types

- **Add Actions**: `#add flash to parcan_l at 5.2s duration 1.5s`
- **Flash Effects**: `#flash all_parcans blue at 10s for 2s`
- **Fade Effects**: `#fade head_el150 from red to blue at 15s for 3s`
- **Strobe Effects**: `#strobe all_parcans at 20s for 1s`
- **Channel Control**: `#set parcan_l red channel to 0.8 at 25s`
- **Presets**: `#preset moving_head Drop at 30s`
- **Canvas Control**: `#render`, `#clear all`
- **Analysis**: `#analyze`, `#analyze context`
- **Help**: `#help`, `#tasks`

## Error Handling

- **Invalid Commands**: Logged and reported to client
- **Execution Failures**: DirectCommandsParser errors are caught and reported
- **Parse Errors**: Regex or validation failures are logged
- **WebSocket Errors**: Send failures are caught to prevent crashes

## Debugging

Enable debug output by checking console logs:

```
🎭 Action command parser initialized for session 12345
🎭 Detected action command in AI response: #add flash to parcan_l at 5.2s
✅ Executed action command: #add flash to parcan_l at 5.2s -> Added flash to parcan_l at 5.20s for 1.50s.
```

## Performance Considerations

- Commands are detected in real-time as the response streams
- Regex processing is minimal and efficient
- Duplicate detection prevents redundant executions
- WebSocket notifications are non-blocking

## Testing

Run the test suite to verify functionality:

```bash
python test_action_command_detection.py
```

This tests:
- Command validation patterns
- Text detection regex
- Mock command execution flow

## Limitations

- Commands must follow exact syntax patterns
- Only supports predefined command types
- Requires active WebSocket connection
- Depends on app state being properly initialized
- May miss commands that are split across multiple chunks (rare)
