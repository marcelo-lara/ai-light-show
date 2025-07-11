from typing import Dict, Callable
from .dmx_canvas import DmxCanvas
from backend.fixture_utils import get_preset_channels

def render_cue(cue: Dict, canvas: DmxCanvas, fixture_config: Dict, start_time: float, end_time: float) -> None:
    """Render a cue into the DMX canvas using painting operations.
    
    Args:
        cue: Dictionary containing cue parameters (preset, timing, effect)
        canvas: DmxCanvas instance to paint onto
        fixture_config: Fixture configuration dictionary
    """
    # Get preset from cue
    preset = cue["preset"]
    effect = cue.get("effect", "full")

    # Get channel values from preset configuration
    channels = get_preset_channels(preset, fixture_config)

    if effect == "full":
        # Paint the full values at the start time
        canvas.paint_frame(start_time, channels)
    elif effect == "fade":
        # Calculate fade parameters
        fade_duration = end_time - start_time
        def fade_fn(t: float) -> Dict[int, int]:
            progress = (t - start_time) / fade_duration
            return {ch: int(val * progress) for ch, val in channels.items()}
        
        # Paint the fade across the duration
        canvas.paint_range(start_time, end_time, fade_fn)
    elif effect == "pulse":
        # Example pulse effect implementation
        pulse_count = cue.get("pulses", 1)
        pulse_interval = (end_time - start_time) / pulse_count
        
        def pulse_fn(t: float) -> Dict[int, int]:
            phase = ((t - start_time) % pulse_interval) / pulse_interval
            return {ch: int(val * (1 - abs(phase - 0.5)*2)) for ch, val in channels.items()}
        
        canvas.paint_range(start_time, end_time, pulse_fn)
    else:
        raise ValueError(f"Unknown effect type: {effect}")
