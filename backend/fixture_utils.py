from backend.chaser_utils import load_chaser_templates
from backend.config import MASTER_FIXTURE_CONFIG, FIXTURE_PRESETS, CHASER_TEMPLATE_PATH
import json

fixture_config = []
fixture_presets = []

def load_fixtures_config():
    global fixture_config, fixture_presets
    try:
        if len(fixture_config)==0:
          with open(MASTER_FIXTURE_CONFIG) as f:
              fixture_config = json.load(f)
              
        if len(fixture_presets)==0:
          with open(FIXTURE_PRESETS) as f:
              fixture_presets = json.load(f)
              print(f"✅ Loaded fixture config with {len(fixture_config)} fixtures and {len(fixture_presets)} presets.")            

        load_chaser_templates()  # Load chaser templates on startup
        return fixture_config, fixture_presets

    except Exception as e:
        print("❌ load_fixtures_config error: ", e)
        return [], []
