from typing import Dict, List
from .dmx_canvas import DmxCanvas
from .render_engine import render_cue

def build_timeline(cues: List[Dict], fixture_config: Dict, song_duration: float, fps: int = 44) -> DmxCanvas:
    """Build a DMX timeline from a list of cues with accurate duration handling."""
    # Calculate actual duration needed (song length + 10% buffer)
    max_cue_end = max((cue.get('end_time', song_duration) for cue in cues), default=song_duration)
    duration = max(max_cue_end * 1.1, song_duration)
    
    # Create canvas with calculated duration
    canvas = DmxCanvas(fps=fps, duration=duration)
    
    # Process cues in chronological order
    for cue in sorted(cues, key=lambda c: c['start_time']):
        if 'start_time' not in cue:
            raise ValueError("Cue missing required 'start_time' field")
            
        start_time = cue['start_time']
        end_time = cue.get('end_time', duration)
        
        # Render cue with time context (in seconds)
        render_cue(
            cue,
            canvas,
            fixture_config,
            start_time=start_time,
            end_time=end_time
        )
    
    canvas.finalize()
    return canvas
