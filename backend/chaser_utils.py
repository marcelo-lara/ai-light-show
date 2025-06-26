import json

from backend.config import CHASER_TEMPLATE_PATH
chasers = None

def beats_to_seconds(beats: float, bpm: float) -> float:
    return (60.0 / bpm) * beats

def get_chasers() -> list[dict]:
    """Returns the list of chasers loaded from the JSON file."""
    global chasers
    if not chasers:
        chasers = load_chaser_templates()
    return chasers

def load_chaser_templates() -> list[dict]:
    global chasers
    """Loads chaser templates from the JSON file."""
    try:
        with open(CHASER_TEMPLATE_PATH) as f:
            chasers = json.load(f)
        return chasers
    except Exception as e:
        print(f"❌ Failed to read chaser_templates.json: {e}")
        return []
    
def expand_chaser_template(chaser_name: str, start_time: float, bpm: float) -> list[dict]:
    """Expands a chaser template into a list of cue dicts, with beat spacing converted to seconds."""
    global chasers

    chaser = next((c for c in chasers if c["name"] == chaser_name), None)
    if not chaser:
        print(f"❌ Chaser '{chaser_name}' not found")
        return []

    preset = chaser.get("preset")
    fixture_ids = chaser.get("fixture_ids", [])
    parameters = chaser.get("parameters", {})
    spacing_beats = parameters.get("beat_spacing", 0.25)

    cues = []
    for i, fid in enumerate(fixture_ids):
        cue_time = round(start_time + beats_to_seconds(i * spacing_beats, bpm), 4)
        cue = {
            "time": cue_time,
            "fixture": fid,
            "preset": preset,
            "parameters": {k: v for k, v in parameters.items() if k != "beat_spacing"},
            "chaser": chaser_name
        }
        cues.append(cue)

    print(f"✅ Expanded chaser '{chaser_name}' into {len(cues)} cues starting at {start_time}s")
    return cues
