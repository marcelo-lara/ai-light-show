from typing import cast

def pre_render_cues(cues, fixture_config, fixture_presets, bpm=120.0, fps=120): 
    timeline = {}
    print(f"🔄 PreRendering timeline for {len(cues)} cues at {fps} FPS with BPM {bpm}")

    def beats_to_ms(beats: float, bpm: float) -> float:
        return (60.0 / bpm) * 1000.0 * beats

    def find_fixture(fid):
        return next((f for f in fixture_config if f["id"] == fid), None)

    def find_preset(pname: str, ftype: str) -> dict | None:
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
        # Validate cue structure
        if not all(key in cue for key in ["fixture", "time", "preset"]):
            print(f"❌ Skipping invalid cue - missing required fields: {cue}")
            continue
            
        try:
            start_time = cue["time"]
            fixture = find_fixture(cue["fixture"])
            if not fixture:
                print(f"⚠️ Skipping cue - fixture not found: {cue['fixture']}")
                continue

            preset_name = cue["preset"]
            # Validate fixture has required properties
            if not fixture or "type" not in fixture:
                print(f"❌ Invalid fixture configuration: {fixture}")
                continue
                
            preset = find_preset(preset_name, fixture["type"])
            
            if not preset:
                print(f"⚠️ Preset not found: '{preset_name}' for {fixture.get('type', 'unknown')} fixture")
                continue

        except KeyError as ke:
            print(f"❌ Invalid cue structure: {str(ke)} in cue: {cue}")
            continue
        except Exception as e:
            print(f"❌ Error processing cue: {str(e)}")
            continue

        # Only process if we have valid fixture and preset
        if not fixture or not preset:
            continue

        # Validate fixture configuration structure and types
        if not all(key in fixture for key in ["name", "channels", "meta"]):
            print(f"❌ Invalid fixture configuration - missing required fields: {fixture}")
            continue
            
        if not isinstance(fixture["channels"], dict) or not fixture["channels"]:
            print(f"❌ Invalid channels configuration for fixture {fixture['name']}")
            continue
            
        if not isinstance(fixture["meta"], dict):
            print(f"❌ Invalid meta configuration for fixture {fixture['name']}")
            continue

        print(f":: Processing cue: {cue['preset']} at {start_time}s for fixture {fixture.get('name', 'unknown')} with preset {preset.get('name', 'unknown')}")
        ch_map = fixture.get("channels", {})
        overrides = cue.get("parameters", {})
        mode = preset.get("mode", "single")

        start_brightness = float(overrides.get("start_brightness", preset.get("parameters", {}).get("start_brightness", 1.0)))

        cycle_duration = 0.0
        if "steps" in preset and preset["steps"]:
            for step in preset["steps"]:
                if step["type"] == "fade":
                    fade_beats = overrides.get("fade_beats", step.get("fade_beats", 0))
                    cycle_duration += beats_to_ms(fade_beats, bpm) / 1000.0
                elif step["type"] == "hold":
                    hold_beats = overrides.get("hold_beats", step.get("duration", 0))
                    cycle_duration += beats_to_ms(hold_beats, bpm) / 1000.0

        step_offset = 0.0
        max_step_time = 0.0

        def render_steps(start_time):
            nonlocal channel_last_values, max_step_time
            t = start_time
            if not preset or "steps" not in preset or preset["steps"] is None:
                print(f"  ⚠️ Skipping cue at {start_time}s: preset or steps missing")
                return
            
            for step in preset["steps"]:
                step_type = step["type"]
                scaled_values = {}
                for ch_name, raw_val in step["values"].items():
                    if ch_name not in ch_map:
                        continue
                    ch_index = ch_map[ch_name]
                    # Final null check and type-safe access
                    # Access validated fixture from outer scope
                    meta = cast(dict, fixture.get("meta", {}))  # type: ignore
                    channel_types = meta.get("channel_types", {})
                        
                    # Type assertion for type checker
                    channel_types = cast(dict, channel_types)
                        
                    is_color = channel_types.get(ch_name, "") == "color"
                    scaled_val = int(raw_val * start_brightness) if is_color else raw_val
                    scaled_values[ch_index] = scaled_val

                if step_type == "set":
                    append_values_at_time(round(t, 4), scaled_values)
                    for ch, v in scaled_values.items():
                        channel_last_values[ch] = (round(t, 4), v)
                    max_step_time = max(max_step_time, t)
                    print(f"  - [set] values at {t:.3f}s: {scaled_values}")

                elif step_type == "fade":
                    fade_beats = overrides.get("fade_beats", step.get("fade_beats", 0))
                    duration = beats_to_ms(fade_beats, bpm) / 1000.0
                    from_vals = {
                        ch: channel_last_values.get(ch, (0.0, 0))[1]
                        for ch in scaled_values
                    }
                    fade_steps = interpolate_steps(from_vals, scaled_values, duration, fps)
                    for offset, fade_vals in fade_steps:
                        t_step = round(t + offset, 4)
                        append_values_at_time(t_step, fade_vals)
                        for ch, v in fade_vals.items():
                            channel_last_values[ch] = (t_step, v)
                    t += duration
                    max_step_time = max(max_step_time, t)
                    print(f"  - [fade] from {from_vals} to {scaled_values} over {duration:.3f}s at {t:.3f}s")

                elif step_type == "hold":
                    hold_beats = overrides.get("hold_beats", step.get("duration", 0))
                    duration = beats_to_ms(hold_beats, bpm) / 1000.0
                    steps = int(duration * fps)
                    for i in range(steps):
                        t_step = round(t + (i / fps), 4)
                        append_values_at_time(t_step, scaled_values)
                        for ch, v in scaled_values.items():
                            channel_last_values[ch] = (t_step, v)
                    t += duration
                    max_step_time = max(max_step_time, t)
                    print(f"  - [hold] keeping {scaled_values} for {duration:.3f}s starting at {start_time:.3f}s")

        if mode == "loop":
            loop_beats = overrides.get("loop_beats", preset.get("loop_beats", 0))
            loop_duration_sec = beats_to_ms(loop_beats, bpm) / 1000.0
            while step_offset < loop_duration_sec:
                render_steps(start_time + step_offset)
                step_offset += cycle_duration
            cue["duration"] = step_offset

        elif mode == "adsr":
            adsr_params = (preset.get("parameters") or {}).get("adsr", {})
            # Validate ADS-R parameters
            if not all(key in adsr_params for key in ["attack", "decay", "sustain", "release"]):
                print(f"❌ Invalid ADS-R configuration in preset {preset.get('name')}")
                continue
                
            try:
                max_value = float(overrides.get("max_value", preset.get("parameters", {}).get("max_value", 1.0)))
                channel_map = preset.get("parameters", {}).get("channel_map", {})
                t = start_time
            except KeyError as e:
                print(f"❌ Missing required parameter in ADS-R config: {str(e)}")
                continue

            def stage(stage_name, from_val, to_rel, duration):
                nonlocal t
                from_vals = {
                    ch_map[ch]: int(from_val * channel_map[ch])
                    for ch in channel_map if ch in ch_map
                }
                to_vals = {
                    ch_map[ch]: int(255 * max_value * to_rel * channel_map[ch])
                    for ch in channel_map if ch in ch_map
                }
                fade_steps = interpolate_steps(from_vals, to_vals, duration, fps)
                for offset, vals in fade_steps:
                    t_step = round(t + offset, 4)
                    append_values_at_time(t_step, vals)
                    for ch, v in vals.items():
                        channel_last_values[ch] = (t_step, v)
                t += duration
                return to_vals

            v_attack = stage("attack", 0, adsr_params["attack"]["to"], adsr_params["attack"]["time"])
            v_decay = stage("decay", list(v_attack.values())[0], adsr_params["decay"]["to"], adsr_params["decay"]["time"])

            # Sustain
            sustain_val = int(255 * max_value * adsr_params["sustain"]["value"])
            sustain_time = adsr_params["sustain"]["time"]
            steps = int(sustain_time * fps)
            for i in range(steps):
                t_step = round(t + (i / fps), 4)
                sustain_vals = {
                    ch_map[ch]: int(sustain_val * channel_map[ch])
                    for ch in channel_map if ch in ch_map
                }
                append_values_at_time(t_step, sustain_vals)
                for ch, v in sustain_vals.items():
                    channel_last_values[ch] = (t_step, v)
            t += sustain_time

            # Release
            stage("release", sustain_val, 0.0, adsr_params["release"]["time"])
            cue["duration"] = round(t - start_time, 3)

        else:
            render_steps(start_time)
            cue["duration"] = round(max_step_time - start_time, 3)

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
