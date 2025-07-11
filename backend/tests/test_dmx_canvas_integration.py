#!/usr/bin/env python
"""
Integration test for DMX Canvas with the render engine.

This script demonstrates how to use the DmxCanvas class with the render engine
to create a DMX timeline from cues.
"""
import json
import time
from backend.render_engine import pre_render_cues
from backend.services.dmx_canvas import DmxCanvas


def load_json_file(filepath):
    """Load a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def test_canvas_with_render_engine():
    """Test the integration of DmxCanvas with the render engine."""
    print("🔄 Loading fixture configuration...")
    fixture_config = load_json_file("fixtures/master_fixture_config.json")
    fixture_presets = load_json_file("fixtures/fixture_presets.json")
    
    # Example cues - in a real scenario, these would come from a file or API
    cues = [
        {
            "time": 0.0,
            "fixture": "par1",
            "preset": "color_fade",
            "parameters": {
                "fade_beats": 4,
                "start_brightness": 1.0
            }
        },
        {
            "time": 2.0,
            "fixture": "par2",
            "preset": "strobe",
            "parameters": {
                "fade_beats": 2,
                "hold_beats": 4
            }
        }
    ]
    
    # Pre-render the cues to get a timeline of channel values
    bpm = 120.0
    fps = 44
    timeline = pre_render_cues(cues, fixture_config, fixture_presets, bpm, fps)
    
    # Create a DMX canvas with the same FPS
    duration = max(timeline.keys()) + 1.0  # Add 1 second padding
    canvas = DmxCanvas(fps=fps, duration=duration)
    
    print(f"🎨 Painting canvas with {len(timeline)} timeline events...")
    start_time = time.time()
    
    # Paint each frame from the timeline onto the canvas
    for t, channel_values in timeline.items():
        canvas.paint_frame(t, channel_values)
    
    end_time = time.time()
    print(f"✅ Canvas painted in {end_time - start_time:.3f} seconds")
    
    # Export the timeline
    dmx_timeline = canvas.export()
    print(f"📦 Exported {len(dmx_timeline)} DMX frames")
    
    # Analyze a few frames
    sample_times = [0.0, 1.0, 2.0, 3.0]
    for t in sample_times:
        frame = canvas.get_frame(t)
        active_channels = [i for i, v in enumerate(frame) if v > 0]
        print(f"🔍 Frame at {t:.1f}s: {len(active_channels)} active channels: {active_channels[:10]}")


if __name__ == "__main__":
    test_canvas_with_render_engine()
