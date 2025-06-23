import json
from backend.dmx_controller import send_artnet, dmx_universe, DMX_CHANNELS, FPS

SONGS_DIR = "/app/static/songs"

# --- Show Timeline ---
emty_packet = [0] * DMX_CHANNELS
song_length = 60  # seconds
show_timeline = []

def get_empty_timeline(_length = song_length ):
    global show_timeline
    show_timeline = [
        {
            "time": round(time, 1), 
            "dmx_universe": emty_packet.copy()
        } for time in [t * 0.1 for t in range(_length * FPS)]
    ]
    return show_timeline

def execute_timeline(time):
    global dmx_universe, show_timeline
    timefound = -1.0  # Default to -1 if no entry found

    # Find the latest timeline entry before the given time
    for entry in reversed(show_timeline):
        if entry["time"] <= time:
            timefound = entry["time"]
            dmx_universe = entry["dmx_universe"]
            break

    print(f"[{timefound:.3f}] Executing timeline at {time:.3f}s: {'.'.join(str(v) for v in dmx_universe[:35])}")
    # Send Art-Net packet 
    send_artnet(dmx_universe)

    return time

def load_song_cues(song_file):
    cue_path = f"{SONGS_DIR}/{song_file}.cues.json"
    try:
        with open(cue_path) as f:
            cues = json.load(f)
        return cues
    except Exception as e:
        return {"error load_song_cues:": str(e)}
    
def render_timeline(fixture_config, fixture_presets, current_song, cues = None, fps=120):
    global show_timeline

    # load the song cues if not provided
    if cues is None:
        cues = load_song_cues(current_song)
        if "error load_song_cues:" in cues:
            print(cues["error load_song_cues:"])
            return []

    # convert cues to a timeline format
    _interpolated_timeline = pre_render_timeline(cues, fixture_config, fixture_presets, current_song, fps)

    # Convert the timeline to a format suitable for the DMX controller
    show_timeline = []
    for event in _interpolated_timeline:
        time = event["time"]
        values = event["values"]
        dmx_universe = [0] * 512
        for ch, val in values.items():
            if 0 <= ch < 512:
                dmx_universe[ch] = val
        show_timeline.append({
            "time": time,
            "dmx_universe": dmx_universe
        })
    
    show_timeline = sorted(show_timeline, key=lambda ev: ev["time"])

    # Save the timeline to a file for debugging
    with open(f"/app/static/songs/{current_song}.timeline.json", "w") as f:
        json.dump(sorted(show_timeline, key=lambda ev: ev["time"]), f, indent=2)

    return show_timeline

def pre_render_timeline(cues, fixture_config, fixture_presets, current_song, fps=120):
    timeline = []

    def find_fixture(fid):
        for f in fixture_config:
            if f["id"] == fid:
                return f
        return None

    def find_preset(pname, ftype):
        for p in fixture_presets:
            if p["name"] == pname and p["type"] == ftype:
                return p
        return None

    def interpolate_steps(start_values, end_values, duration, fps):
        steps = []
        interval = 1.0 / fps
        total_steps = int(duration / interval)
        for i in range(1, total_steps + 1):
            t = i / total_steps
            step_vals = {
                ch: int(start_values[ch] + t * (end_values[ch] - start_values[ch]))
                for ch in start_values
            }
            steps.append((round(i * interval, 4), step_vals))
        return steps

    for cue in cues:
        start_time = cue["time"]
        fixture = find_fixture(cue["fixture"])
        if not fixture:
            continue

        preset = find_preset(cue["preset"], fixture["type"])
        if not preset:
            continue

        ch_map = fixture["channels"]
        overrides = cue.get("parameters", {})
        loop = preset.get("mode") == "loop"
        loop_duration = overrides.get("loop_duration", 1000) / 1000.0  # ms → sec

        step_offset = 0
        while True:
            for step in preset["steps"]:
                t = start_time + step_offset
                if step["type"] == "set":
                    values = {
                        ch_map[k]: v for k, v in step["values"].items() if k in ch_map
                    }
                    timeline.append({"time": round(t, 4), "values": values})

                elif step["type"] == "fade":
                    duration = overrides.get("duration", step["duration"]) / 1000.0
                    to_vals = {
                        ch_map[k]: v for k, v in step["values"].items() if k in ch_map
                    }
                    from_vals = {ch: 0 for ch in to_vals}
                    fade_steps = interpolate_steps(from_vals, to_vals, duration, fps)
                    for offset, fade_vals in fade_steps:
                        timeline.append({
                            "time": round(t + offset, 4),
                            "values": fade_vals
                        })
                    step_offset += duration
                    
            if loop:
                step_offset += loop_duration
                if step_offset > loop_duration:
                    break
            else:
                break
    
    # save the timeline to a file for debugging
    with open(f"/app/static/songs/{current_song}.timeline_events.json", "w") as f:
        json.dump(sorted(timeline, key=lambda ev: ev["time"]), f, indent=2)
    print(f"✅ Rendered {len(timeline)} timeline events from {len(cues)} cues.")

    return sorted(timeline, key=lambda ev: ev["time"])
