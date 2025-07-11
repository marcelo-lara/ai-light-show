from typing import Dict
from backend.chaser_utils import load_chaser_templates 
from backend.config import MASTER_FIXTURE_CONFIG, FIXTURE_PRESETS, CHASER_TEMPLATE_PATH
import json

fixture_config = []
fixture_presets = []

def load_fixtures_config(force_reload=False):
    global fixture_config, fixture_presets
    try:
        if force_reload or len(fixture_config)==0:
          with open(MASTER_FIXTURE_CONFIG) as f:
              fixture_config = json.load(f)

        if force_reload or len(fixture_presets)==0:
          with open(FIXTURE_PRESETS) as f:
              fixture_presets = json.load(f)
              print(f"✅ Loaded fixture config with {len(fixture_config)} fixtures and {len(fixture_presets)} presets.")            

              chasers = load_chaser_templates()  # Load chaser templates on startup
              return fixture_config, fixture_presets, chasers

    except Exception as e:
        print("❌ load_fixtures_config error: ", e)
        return [], [], []

def get_preset_channels(preset_name: str, fixture_config: dict) -> Dict[int, int]:
    """Get channel values for a given preset from fixture configuration."""
    preset = fixture_config["presets"].get(preset_name, {})
    return {
        channel["address"]: channel["value"]
        for channel in preset.get("channels", [])
    }
