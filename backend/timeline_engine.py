import json
from backend.dmx_controller import send_artnet, dmx_universe, DMX_CHANNELS, FPS

# --- Show Timeline ---
emty_packet = [0] * DMX_CHANNELS
song_length = 60  # seconds
show_timeline: dict[float, list[int]] = {}

skipLog = False

# Execute the timeline at a given time
def execute_timeline(current_time):
    """ 
    Execute the DMX timeline at the specified time.
    """
    global dmx_universe, show_timeline, skipLog
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

    skipLog = False
    print(f"[{timefound:.3f}] {current_time:.3f}s -> {'.'.join(f'{v:3d}' for v in dmx_universe[:30])}")

    send_artnet(dmx_universe)
    return timefound

# Render the timeline for a song based on its cues
def render_timeline(fixture_config, fixture_presets, current_song, cues=None, fps=120):
    """ 
    Render the timeline for a song based on its cues.
    This function processes the cues and generates a timeline of DMX frames.
    It returns a dictionary mapping timestamps to an Artnet packe frame.
    """
    global show_timeline

    if cues is None:
        print(f"❌ empty cues, cannot render timeline for {current_song}")
        return {}

    timeline = pre_render_timeline(cues, fixture_config, fixture_presets)
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
        f.write(f"time  | " + " ".join(f"{i:03d}" for i in range(1, 36)) + "\n")
        for t in sorted(show_timeline.keys()):
            d = show_timeline[t]
            f.write(f"{t:.3f} | {'.'.join(f'{v:3d}' for v in d[:40])}\n")

    print(f"✅ Rendered {len(show_timeline)} frames -> {len(show_timeline)/fps:.3f}s")
    return show_timeline

def pre_render_timeline(cues, fixture_config, fixture_presets, fps=120): 
    timeline = {}

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

    def append_values_at_time(t, values):
        if t not in timeline:
            timeline[t] = {}
        for ch, val in values.items():
            timeline[t][ch] = val

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
        mode = preset.get("mode", "single")

        # Calculate one full cycle duration
        cycle_duration = 0.0
        for step in preset["steps"]:
            if step["type"] == "fade":
                cycle_duration += overrides.get("fade_duration", step.get("duration", 0)) / 1000.0

        step_offset = 0.0

        def render_steps(start_time):
            nonlocal channel_last_values
            t = start_time
            for step in preset["steps"]:
                step_type = step["type"]

                if step_type == "set":
                    values = {ch_map[k]: v for k, v in step["values"].items() if k in ch_map}
                    append_values_at_time(round(t, 4), values)
                    for ch, v in values.items():
                        channel_last_values[ch] = (round(t, 4), v)
                    print(f"  - [set] values at {t:.3f}s: {values}")

                elif step_type == "fade":
                    duration = overrides.get("fade_duration", step.get("duration", 0)) / 1000.0
                    to_vals = {ch_map[k]: v for k, v in step["values"].items() if k in ch_map}
                    from_vals = {
                        ch: channel_last_values.get(ch, (0.0, 0))[1]
                        for ch in to_vals
                    }
                    fade_steps = interpolate_steps(from_vals, to_vals, duration, fps)
                    for offset, fade_vals in fade_steps:
                        t_step = round(t + offset, 4)
                        append_values_at_time(t_step, fade_vals)
                        for ch, v in fade_vals.items():
                            channel_last_values[ch] = (t_step, v)
                    t += duration
                    print(f"  - [fade] from {from_vals} to {to_vals} over {duration:.3f}s at {t:.3f}s")

        if mode == "loop":
            loop_duration_sec = overrides.get("loop_duration", 1000) / 1000.0
            while step_offset < loop_duration_sec:
                render_steps(start_time + step_offset)
                step_offset += cycle_duration

        else:  # mode == "single"
            render_steps(start_time)

    # 🛡️ Always-arm all fixtures across full duration
    last_t = max(timeline.keys(), default=0.0)
    total_steps = int(last_t * fps)

    for fixture in fixture_config:
        arm = fixture.get("arm")
        if arm:
            ch_map = fixture["channels"]
            arm_ch_name = arm["channel"]
            arm_ch_num = ch_map.get(arm_ch_name)
            if arm_ch_num is not None:
                for i in range(total_steps + 1):
                    t = round(i / fps, 4)
                    append_values_at_time(t, {arm_ch_num: arm["value"]})

    print(f"✅ PreRendered {sum(len(v) for v in timeline.values())} channel events from {len(cues)} cues.")
    return timeline
