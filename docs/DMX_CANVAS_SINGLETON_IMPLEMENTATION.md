# DMX Canvas Singleton Implementation

## 🎯 Overview
The `DmxCanvas` class has been converted to a **singleton pattern** to ensure only one DMX canvas instance exists throughout the AI Light Show application. This prevents data conflicts and maintains consistency across all services.

## 🔧 Implementation Details

### Singleton Pattern Features
1. **Single Instance**: Only one `DmxCanvas` object can exist at any time
2. **Shared State**: All references point to the same instance and data
3. **Lazy Initialization**: Instance created on first access
4. **Reset Capability**: Can create new instance with different parameters when needed
5. **State Persistence**: Canvas data persists across all references

### Key Methods

#### `__new__()` - Singleton Enforcement
```python
def __new__(cls, fps: int = 44, duration: float = 300.0, debug: Optional[bool] = False):
    if cls._instance is None:
        cls._instance = super(DmxCanvas, cls).__new__(cls)
    return cls._instance
```
- Ensures only one instance exists
- Subsequent calls return existing instance
- Parameters from second+ calls are ignored

#### `__init__()` - One-Time Initialization
```python
def __init__(self, fps: int = 44, duration: float = 300.0, debug: Optional[bool] = False):
    if hasattr(self, '_initialized') and self._initialized:
        # Skip re-initialization
        return
    # Initialize canvas properties...
    self._initialized = True
```
- Only runs initialization code once
- Subsequent calls are ignored with warning message
- Preserves original parameters

#### `get_instance()` - Safe Access
```python
@classmethod
def get_instance(cls) -> 'DmxCanvas':
    if cls._instance is None:
        cls._instance = cls()
    return cls._instance
```
- Provides safe way to access singleton
- Creates instance if none exists
- Uses default parameters for new instance

#### `reset_instance()` - Parameter Changes
```python
@classmethod  
def reset_instance(cls, fps: int = 44, duration: float = 300.0, debug: Optional[bool] = False) -> 'DmxCanvas':
    cls._instance = None
    return cls(fps=fps, duration=duration, debug=debug)
```
- Destroys existing instance
- Creates new instance with specified parameters
- All existing references will point to new instance

#### `is_initialized()` - Status Check
```python
@classmethod
def is_initialized(cls) -> bool:
    return cls._instance is not None and hasattr(cls._instance, '_initialized') and cls._instance._initialized
```
- Checks if singleton has been created and initialized
- Useful for conditional logic

### `clear_canvas()` - Data Reset
```python
def clear_canvas(self) -> None:
    self._canvas.fill(0)
    self._timeline.clear()
```
- Clears all canvas data while preserving singleton instance
- Resets all channels to zero
- Maintains same canvas dimensions and parameters

## 🎯 Usage Patterns

### Standard Usage
```python
# All these create/return the same instance
canvas1 = DmxCanvas(fps=30, duration=10.0)
canvas2 = DmxCanvas(fps=60, duration=20.0)  # Parameters ignored
canvas3 = DmxCanvas.get_instance()

# All references point to same object
assert canvas1 is canvas2 is canvas3  # True

# Shared state across all references
canvas1.paint_frame(5.0, {0: 255})
frame = canvas2.get_frame(5.0)  # Same data
```

### Parameter Changes
```python
# Change canvas parameters (creates new instance)
new_canvas = DmxCanvas.reset_instance(fps=60, duration=20.0)

# Old references now point to new instance
old_canvas = DmxCanvas()  # Points to new instance
assert new_canvas is old_canvas  # True
```

### App State Integration
```python
from backend.models.app_state import app_state

# Set singleton in app state
app_state.dmx_canvas = DmxCanvas(fps=44, duration=300.0)

# All future DmxCanvas() calls return same instance
canvas = DmxCanvas()
assert canvas is app_state.dmx_canvas  # True
```

### Conditional Initialization
```python
if not DmxCanvas.is_initialized():
    canvas = DmxCanvas(fps=44, duration=300.0)
else:
    canvas = DmxCanvas.get_instance()
```

## ✅ Benefits

### Data Consistency
- **Single Source of Truth**: All components use same canvas data
- **No Conflicts**: Prevents multiple canvas instances with different data
- **Shared State**: Changes visible across all references immediately

### Memory Efficiency  
- **Single Instance**: Only one large NumPy array in memory
- **No Duplication**: Prevents accidental creation of multiple canvases
- **Resource Optimization**: Efficient memory usage for large timelines

### Application Architecture
- **Global Access**: Canvas available anywhere in application
- **Service Integration**: Works seamlessly with app_state singleton
- **Clear Ownership**: One instance eliminates confusion about which canvas to use

### Debugging & Testing
- **Predictable State**: Always know which canvas instance is active
- **Easy Reset**: Can reset for tests without affecting other components
- **Status Checking**: Can verify if canvas exists before using

## 🔄 Migration Impact

### Existing Code Compatibility
```python
# Old code continues to work unchanged
canvas = DmxCanvas(fps=44, duration=300.0)
canvas.paint_frame(2.0, {10: 255})
frame = canvas.get_frame(2.0)

# Multiple instantiations now return same object (instead of creating new ones)
canvas2 = DmxCanvas(fps=60, duration=200.0)  # Same as canvas1, parameters ignored
```

### App State Integration
```python
# app_state.dmx_canvas automatically uses singleton
app_state.dmx_canvas = DmxCanvas()

# All services now share same canvas instance
from backend.services.dmx.dmx_canvas import DmxCanvas
canvas = DmxCanvas()  # Same as app_state.dmx_canvas
```

### Testing Considerations
```python
# Reset canvas between tests
def setup_test():
    DmxCanvas.reset_instance(fps=44, duration=10.0, debug=True)
    
def test_something():
    canvas = DmxCanvas()
    # Test with clean canvas
```

## 📊 Test Results

✅ **Singleton Behavior**: Multiple instantiations return same object  
✅ **State Persistence**: Data shared across all references  
✅ **Parameter Isolation**: Subsequent calls ignore parameters  
✅ **Reset Functionality**: Can create new instance with different parameters  
✅ **Memory Consistency**: Single instance in memory at all times  
✅ **App State Integration**: Works seamlessly with global app state  
✅ **Clear Operations**: Canvas can be cleared while preserving singleton  
✅ **Status Tracking**: Can check initialization status reliably  

The singleton implementation ensures the DMX Canvas maintains consistency and prevents conflicts while preserving all existing functionality and API compatibility.
