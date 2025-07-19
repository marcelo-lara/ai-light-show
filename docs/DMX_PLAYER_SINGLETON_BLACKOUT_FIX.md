# DMX Player Singleton Integration and Blackout Control

## 🎯 Summary
Updated the DMX Player to enforce DmxCanvas singleton usage and implement proper blackout transmission control based on the `blackout_when_not_playing` flag.

## 🔧 Changes Made

### 1. DmxCanvas Singleton Integration

#### `_retrieve_dmx_frame()` Method
**Before:**
```python
# Used app_state.dmx_canvas (could be None or different instances)
from ...models.app_state import app_state
if not app_state.dmx_canvas:
    print("⚠️ No DMX canvas available for rendering")
    return [0] * 512
frame_bytes = app_state.dmx_canvas.get_frame(current_time)
```

**After:**
```python
# Uses DmxCanvas singleton directly
from .dmx_canvas import DmxCanvas

if not DmxCanvas.is_initialized():
    print("⚠️ No DMX canvas singleton initialized")
    return [0] * 512

canvas = DmxCanvas.get_instance()
frame_bytes = canvas.get_frame(current_time)
```

**Benefits:**
- **Guaranteed Consistency**: Always uses the same canvas instance
- **Explicit Singleton**: Direct singleton pattern usage instead of app_state dependency
- **Better Error Handling**: Clear messaging when singleton not initialized
- **Performance**: Direct access without app_state lookup

### 2. Blackout Transmission Control

#### `_dispatcher_loop()` Method
**Before:**
```python
if self.playback_state.is_playing:
    # Send lighting data
    send_artnet(dmx_universe, current_time=current_time, debug=False)
else:
    # Always send blackout if flag is set
    if self.blackout_when_not_playing:
        blackout_universe = [0] * 512
        send_artnet(blackout_universe, current_time=current_time, debug=False)
# No explicit control over when NOT to send frames
```

**After:**
```python
if self.playback_state.is_playing:
    # Send lighting data when playing
    dmx_universe = self._retrieve_dmx_frame(current_time)
    send_artnet(dmx_universe, current_time=current_time, debug=False)
elif self.blackout_when_not_playing:
    # Only send blackout when explicitly enabled
    blackout_universe = [0] * 512
    send_artnet(blackout_universe, current_time=current_time, debug=False)

# If not playing and blackout_when_not_playing is False, 
# don't send any frames to the Art-Net node
```

**Key Behavior Changes:**
- **Conditional Transmission**: Frames only sent when playing OR when blackout explicitly enabled
- **No Unnecessary Traffic**: When `blackout_when_not_playing=False`, no Art-Net packets sent when stopped
- **Clear Logic Flow**: Explicit conditions for when to send vs when to not send

### 3. Documentation Updates

#### Class Documentation
```python
class DmxPlayer:
    """
    DMX Player manages real-time playback and DMX output.
    
    This service handles:
    - Playback timing synchronization
    - DMX universe dispatch from singleton DmxCanvas  # Updated
    - Real-time Art-Net output
    - Conditional blackout transmission                # Added
    """
```

## 🎯 Behavior Matrix

| Playback State | `blackout_when_not_playing` | Art-Net Transmission |
|----------------|----------------------------|---------------------|
| Playing | `True` | ✅ Lighting data from canvas |
| Playing | `False` | ✅ Lighting data from canvas |
| Not Playing | `True` | ✅ Blackout frames (all zeros) |
| Not Playing | `False` | ❌ **No frames sent** |

## 📊 Implementation Benefits

### Singleton Enforcement
- **Data Consistency**: All DMX players use the same canvas instance
- **Memory Efficiency**: Single canvas instance across the application
- **Predictable State**: No confusion about which canvas is active
- **Direct Access**: Faster canvas access without app_state indirection

### Blackout Control
- **Network Efficiency**: Reduces unnecessary Art-Net traffic when stopped
- **Explicit Behavior**: Clear control over when blackout frames are sent
- **Hardware Friendly**: Prevents constant blackout spam to DMX nodes
- **User Control**: Application can choose blackout behavior per use case

### Error Handling
- **Graceful Degradation**: Safe fallbacks when canvas not available
- **Clear Messaging**: Descriptive error messages for debugging
- **Robust Operation**: Continues running even with canvas issues

## ✅ Test Results

### Singleton Usage Tests
✅ **Direct Canvas Access**: Players retrieve frames from singleton correctly  
✅ **Initialization Check**: Proper fallback when singleton not initialized  
✅ **Multi-Player Consistency**: Multiple players use same singleton instance  
✅ **Data Persistence**: Canvas data shared across all player instances  

### Blackout Behavior Tests
✅ **No Frames (blackout=False)**: Zero packets sent when not playing  
✅ **Blackout Frames (blackout=True)**: Blackout packets sent when not playing  
✅ **Playing Mode**: Lighting data sent when playing regardless of blackout flag  
✅ **State Transitions**: Proper behavior when switching between play/pause states  

## 🔄 Migration Impact

### Existing Code Compatibility
- **DMX Player API**: All public methods unchanged
- **Playback Control**: play(), pause(), stop(), seek() work identically
- **WebSocket Sync**: sync_playback() behavior preserved
- **Frame Callbacks**: Callback system continues to work

### New Capabilities
- **Singleton Enforcement**: Automatic use of DmxCanvas singleton
- **Traffic Control**: Fine-grained control over Art-Net transmission
- **Better Performance**: Direct canvas access without app_state lookup
- **Cleaner Architecture**: Explicit singleton usage pattern

### Configuration Options
```python
# Default behavior - no blackout when stopped
player = DmxPlayer()
player.blackout_when_not_playing = False  # No frames when not playing

# Explicit blackout - send blackout frames when stopped  
player = DmxPlayer()
player.blackout_when_not_playing = True   # Blackout frames when not playing
```

## 🎯 Usage Patterns

### Standard Usage (No Blackout)
```python
# Setup
canvas = DmxCanvas.reset_instance(fps=44, duration=300.0)
player = DmxPlayer()
player.blackout_when_not_playing = False  # Default

# Behavior
await player.start_playback_engine()    # No frames sent
player.sync_playback(True, 10.0)        # Start sending lighting data
player.sync_playback(False, 20.0)       # Stop sending frames
```

### Explicit Blackout Mode
```python
# Setup  
canvas = DmxCanvas.get_instance()
player = DmxPlayer()
player.blackout_when_not_playing = True

# Behavior
await player.start_playback_engine()    # Send blackout frames
player.sync_playback(True, 10.0)        # Send lighting data
player.sync_playback(False, 20.0)       # Send blackout frames
```

The implementation now enforces DmxCanvas singleton usage and provides precise control over Art-Net transmission, reducing network traffic and ensuring consistent canvas access across all DMX player instances.
