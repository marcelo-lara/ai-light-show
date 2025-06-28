import json
from backend.dmx_controller import send_artnet, dmx_universe, DMX_CHANNELS, FPS
from backend.render_engine import pre_render_cues

# --- Show Timeline ---
emty_packet = [0] * DMX_CHANNELS
song_length = 60  # seconds
show_timeline: dict[float, list[int]] = {}

last_timefound = -1.0
skipLog = False

# Execute the timeline at a given time
def execute_timeline(current_time):
    """ 
    Execute the DMX timeline at the specified time.
    """
    global dmx_universe, show_timeline, skipLog, last_timefound
    timefound = -1.0

    # Find the latest timestamp <= current_time
    available_times = [t for t in show_timeline if t <= current_time]
    if not available_times:
        if not skipLog:
            print(f"[{current_time:.3f}] No available timeline frames for {current_time:.3f}s")
        skipLog = True
        return current_time  # Nothing to send

    timefound = max(available_times)
    dmx_universe = show_timeline[timefound]

    send_artnet(dmx_universe)
    return timefound

# Render the timeline for a song based on its cues
def render_timeline(fixture_config, fixture_presets, current_song, cues=None, bpm=120.0, fps=FPS):
    """ 
    Render the timeline for a song based on its cues.
    This function processes the cues and generates a timeline of DMX frames.
    It returns a dictionary mapping timestamps to an Artnet packet frame.
    """
    global show_timeline

    if cues is None:
        print(f"❌ empty cues, cannot render timeline for {current_song}")
        return {}

    timeline = pre_render_cues(cues, fixture_config, fixture_presets, bpm, fps)
    show_timeline = {}

    last_frame = [0] * 512
    for t in sorted(timeline.keys()):
        frame = last_frame.copy()
        for ch, v in timeline[t].items():
            if 0 <= ch < 512:
                frame[ch - 1] = v  # DMX channels are 1-based in mapping
        show_timeline[t] = frame
        last_frame = frame

    # Debug log output
    with open(f"/app/static/songs/{current_song}.timeline.log", "w") as f:
        f.write(f"// Timeline for {current_song}\n")
        f.write(f"// Rendered from {len(cues)} cues\n")
        f.write(f"// Total frames: {len(show_timeline)}\n")
        f.write(f"// FPS: {fps}\n")
        f.write(f"// Length: {len(show_timeline) / fps:.2f} seconds\n")
        f.write(f"time  | " + " ".join(f"{i:03d}." for i in range(1, 36)) + "\n")
        for t in sorted(show_timeline.keys()):
            d = show_timeline[t]
            f.write(f"{t:.3f} | {'.'.join(f'{v:3d}' for v in d[:40])}\n")

    max_time = max(show_timeline.keys()) if show_timeline else 0
    print(f"✅ Rendered {len(show_timeline)} frames -> {max_time:.3f}s")
    return show_timeline
