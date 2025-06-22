# timeline_engine.py

def render_timeline(cues, fixture_map, preset_definitions):
    timeline = []
    for cue in cues:
        fixture = fixture_map.get(cue["fixture"])
        preset = next((p for p in preset_definitions if p["name"] == cue["preset"]), None)
        if not fixture or not preset:
            continue

        base_time = cue["time"]
        duration = cue.get("duration", 0)
        params = cue.get("parameters", {})
        steps = preset.get("steps", [])

        time_cursor = base_time
        loop = preset.get("mode") == "loop"
        loop_duration = params.get("loop_duration", duration)
        loop_iterations = max(1, loop_duration // sum(
            step.get("duration", 0) if isinstance(step.get("duration", 0), int) else params.get(step["duration"], 0)
            for step in steps
        ))

        for iteration in range(loop_iterations):
            for step in steps:
                step_type = step.get("type")
                values = step.get("values", {})
                step_duration = step.get("duration", 0)
                if isinstance(step_duration, str):
                    step_duration = params.get(step_duration, 0)

                if step_type == "set":
                    timeline.append({
                        "time": round(time_cursor, 3),
                        "values": {
                            fixture["channels"][ch]: val
                            for ch, val in values.items()
                            if ch in fixture["channels"]
                        }
                    })
                elif step_type == "fade":
                    steps_count = max(1, step_duration // 50)
                    for i in range(steps_count):
                        progress = (i + 1) / steps_count
                        interpolated = {
                            fixture["channels"][ch]: round(progress * val)
                            for ch, val in values.items()
                            if ch in fixture["channels"]
                        }
                        timeline.append({
                            "time": round(time_cursor + i * (step_duration / steps_count), 3),
                            "values": interpolated
                        })
                    time_cursor += step_duration

            if not loop:
                break
            time_cursor = base_time + (iteration + 1) * sum(
                step.get("duration", 0) if isinstance(step.get("duration", 0), int) else params.get(step["duration"], 0)
                for step in steps
            )

    return sorted(timeline, key=lambda x: x["time"])