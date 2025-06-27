from backend.config import SONGS_DIR
from pathlib import Path
import json


songs_list = []


def get_songs_list() -> list[str]:
  """
  Returns a list of available songs in the songs folder.
  """
  from pathlib import Path

  # Ensure the SONGS_DIR exists
  if not SONGS_DIR.exists():
      return []

  # List all mp3 files in the SONGS_DIR
  songs_list = list(SONGS_DIR.glob("*.mp3"))
  
  # Return a list of song names without the file extension
  return [song.stem for song in songs_list if song.is_file()]

def load_song(song_name: str) -> str:
    """
    Loads a song by its name from the SONGS_DIR.
    Returns the full path to the song file.
    """

    song_path = SONGS_DIR / f"{song_name}.mp3"
    
    if not song_path.exists():
        raise FileNotFoundError(f"Song '{song_name}' not found in {SONGS_DIR}")

    return str(song_path)

def load_song_metadata(song_name: str) -> dict:
    """
    Loads song metadata from a JSON file.
    Returns a dictionary with the metadata.
    """
    from pathlib import Path
    import json

    song_file = song_name + '.mp3' if not song_name.endswith('.mp3') else song_name
    metadata_path = SONGS_DIR / f"{song_file}.metadata.json"
    
    if not metadata_path.exists():
        return {
          "length": 135,
          "style": "electronic",
          "title": "Born Slippy",
          "bpm": 140,
          "arrangement": []
        }

    with open(metadata_path, 'r') as f:
        return json.load(f)

def save_song_metadata(song_name, metadata):
    song_file = song_name + '.mp3' if not song_name.endswith('.mp3') else song_name
    
    metadata_path = SONGS_DIR / f"{song_file}.metadata.json"
    try:
        metadata_path.write_text(json.dumps(metadata, indent=2))
        print(f"💾 Saved metadata to {metadata_path}")
    except Exception as e:
        print(f"❌ save_song_metadata error: {e}")

