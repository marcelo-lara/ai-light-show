from pathlib import Path

### Paths
BASE_DIR = Path("/app/static") if Path("/app/static").exists() else Path(__file__).parent.parent

## DMX Related
FIXTURES_FILE = BASE_DIR / "fixtures/fixtures.json"
MASTER_FIXTURE_CONFIG = BASE_DIR / "fixtures/master_fixture_config.json"
FIXTURE_PRESETS = BASE_DIR / "fixtures/fixture_presets.json"



## Song Related
SONGS_DIR = BASE_DIR / "songs"
SONGS_TEMP_DIR = BASE_DIR / "songs/temp"
LOCAL_TEST_SONG_PATH = "/home/darkangel/ai-light-show/songs/born_slippy.mp3"

## AI Related
AI_CACHE =  Path("/root/.cache") if Path("/app/static").exists() else BASE_DIR / ".cache"

if __name__ == "__main__":
    print(f"Base Directory: {BASE_DIR}")
    print(f"Master Fixture Config: {MASTER_FIXTURE_CONFIG}")
    print(f"Fixture Presets: {FIXTURE_PRESETS}")
    print(f"Songs Directory: {SONGS_DIR}")
    print(f"Songs Temp Directory: {SONGS_TEMP_DIR}")
    print(f"Local Test Song Path: {LOCAL_TEST_SONG_PATH}")
    print(f"AI Cache Directory: {AI_CACHE}")