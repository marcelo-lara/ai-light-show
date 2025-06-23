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

    print(f"[{timefound:.3f}] {time:.3f}s -> {'.'.join(f'{v:3d}' for v in dmx_universe[:30])}")
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
    
def render_timeline(fixture_config, fixture_presets, current_song, cues=None, fps=120):
    global show_timeline

    # Load cues if not passed in
    if cues is None:
        cues = load_song_cues(current_song)
        if "error load_song_cues:" in cues:
            print(cues["error load_song_cues:"])
            return []

    # Generate raw timeline events
    interpolated = pre_render_timeline(cues, fixture_config, fixture_presets, current_song, fps)

    # Merge events by time
    merged = {}
    for ev in interpolated:
        t = ev["time"]
        vals = ev["values"]
        if t not in merged:
            merged[t] = {}
        merged[t].update(vals)

    # Sort and build show_timeline
    show_timeline = []
    last_frame = [0] * 512
    for t in sorted(merged.keys()):
        frame = last_frame.copy()
        for ch, v in merged[t].items():
            if 0 <= ch < 512:
                frame[ch-1] = v
        show_timeline.append({
            "time": t,
            "dmx_universe": frame
        })
        last_frame = frame

    # Debug output
    with open(f"/app/static/songs/{current_song}.timeline.log", "w") as f:
        f.write(f"// Timeline for {current_song}\n")
        f.write(f"// Rendered from {len(cues)} cues\n")
        f.write(f"// Total events: {len(show_timeline)}\n")
        f.write(f"// FPS: {fps}\n")
        f.write(f"// Length: {len(show_timeline) / fps:.2f} seconds\n")
        f.write(f"time  | " + " ".join(f"{i:03d}" for i in range(1, 36)) + "\n")
        for ev in show_timeline[:100]:
            t = ev["time"]
            d = ev["dmx_universe"]
            f.write(f"{t:.3f} | {'.'.join(f'{v:03d}' for v in d[:35])}\n")

    print(f"✅ Rendered {len(show_timeline)} frames -> {len(show_timeline)/fps}s")
    return show_timeline

def pre_render_timeline(cues, fixture_config, fixture_presets, current_song, fps=120):
    timeline = []

    def find_fixture(fid):
        return next((f for f in fixture_config if f["id"] == fid), None)

    def find_preset(pname, ftype):
        return next((p for p in fixture_presets if p["name"] == pname and p["type"] == ftype), None)

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

    channel_last_values = {}

    for cue in cues:
        start_time = cue["time"]
        fixture = find_fixture(cue["fixture"])
        if not fixture:
            continue

        preset = find_preset(cue["preset"], fixture["type"])
        if not preset:
            continue

        print(f":: Processing cue: {cue['preset']} at {start_time}s for fixture {fixture['name']} with preset {preset['name']}")
        ch_map = fixture["channels"]
        overrides = cue.get("parameters", {})

        # determine preset mode
        print(f"  mode: {preset['mode']}")

        loop_duration_sec = overrides.get("loop_duration", 1000) / 1000.0
        step_offset = 0.0

        # Calculate total duration for one full preset cycle
        cycle_duration = 0.0
        for step in preset["steps"]:
            if step["type"] == "fade":
                cycle_duration += overrides.get("fade_duration", step["duration"]) / 1000.0
        print(f"  - Cycle duration: {cycle_duration:.3f}s")


        while step_offset < loop_duration_sec:
            t = start_time + step_offset
            for step in preset["steps"]:
                step_type = step["type"]

                if step_type == "set":
                    values = {ch_map[k]: v for k, v in step["values"].items() if k in ch_map}
                    timeline.append({"time": round(t, 4), "values": values})
                    for ch, v in values.items():
                        channel_last_values[ch] = (round(t, 4), v)
                    print(f"  - [set] values at {t:.3f}s: {values}")

                elif step_type == "fade":
                    duration = overrides.get("fade_duration", step["duration"]) / 1000.0
                    to_vals = {ch_map[k]: v for k, v in step["values"].items() if k in ch_map}
                    from_vals = {
                        ch: channel_last_values.get(ch, (0.0, 0))[1]
                        for ch in to_vals
                    }
                    fade_steps = interpolate_steps(from_vals, to_vals, duration, fps)
                    for offset, fade_vals in fade_steps:
                        t_step = round(t + offset, 4)
                        timeline.append({"time": t_step, "values": fade_vals})
                        for ch, v in fade_vals.items():
                            channel_last_values[ch] = (t_step, v)
                    t += duration
                    print(f"  - [fade] from {from_vals} to {to_vals} over {duration:.3f}s at {t:.3f}s")

            step_offset += cycle_duration

    # 🛡️ Always-arm all fixtures across full duration
    last_t = max((ev["time"] for ev in timeline), default=0.0)
    total_steps = int(last_t * fps)
    arm_inserts = []

    for fixture in fixture_config:
        arm = fixture.get("arm")
        if arm:
            ch_map = fixture["channels"]
            arm_ch_name = arm["channel"]
            arm_ch_num = ch_map.get(arm_ch_name)
            if arm_ch_num is not None:
                for i in range(total_steps + 1):
                    t = round(i / fps, 4)
                    arm_inserts.append({"time": t, "values": {arm_ch_num: arm["value"]}})

    timeline += arm_inserts
    timeline = sorted(timeline, key=lambda ev: ev["time"])

    with open(f"/app/static/songs/{current_song}.timeline_events.json", "w") as f:
        json.dump(timeline, f, indent=2)

    print(f"✅ PreRendered {len(timeline)} timeline events from {len(cues)} cues.")
    return timeline
