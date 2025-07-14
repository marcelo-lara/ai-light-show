## Load metadata hints from the hints folder
# This module is responsible for loading metadata hints for songs, such as arrangement and key moments.
import json
import logging
from models.song_metadata import SongMetadata, Section
logger = logging.getLogger(__name__)

def load_arrangement_from_hints(song: SongMetadata) -> SongMetadata:
    """
    Load the arrangement from the hints folder for the given song.
    file location: "/songs/hints/<song_name>.segments.json"

    Args:
        song (SongMetadata): The song metadata object to load arrangement into.
    Returns:
        SongMetadata: The updated song metadata object with arrangement loaded (if exists).
    """
    file_path = f"{song.songs_folder}/hints/{song.song_name}.segments.json"
    try:
        with open(file_path, 'r') as f:
            # Convert raw dicts to Section objects
            raw_sections = json.load(f)
            song.arrangement = []
            for section in raw_sections:
                try:
                    # Map 'label' to 'name' and add required 'prompt' field
                    section_data = section.copy()
                    section_data['name'] = section_data.pop('label')
                    section_data['prompt'] = ""  # Add empty prompt field
                    song.arrangement.append(Section(**section_data))
                except TypeError as e:
                    print(f"Warning: Invalid section data - {e}")
                    print(f"Section data: {section}")
        logger.info(f" 📖 Arrangement loaded from {file_path}")

    except FileNotFoundError:
        logger.info(f" ⚠️ Arrangement file not found [{file_path}]")
        pass
    return song

def load_key_moments_from_hints(song: SongMetadata) -> SongMetadata:
    """
    Load the key_moments from the hints folder for the given song.
    file location: "/songs/hints/<song_name>.key_moments.json"

    Args:
        song (SongMetadata): The song metadata object to load key_moments into.
    Returns:
        SongMetadata: The updated song metadata object with key_moments loaded (if exists).
    """
    file_path = f"{song.songs_folder}/hints/{song.song_name}.key_moments.json"
    try:
        with open(file_path, 'r') as f:
            song.key_moments = json.load(f)
        logger.info(f" 📖 KeyMoments loaded from {file_path}")

    except FileNotFoundError:
        logger.info(f" ⚠️ KeyMoments file not found [{file_path}]")
        pass
    return song

def load_chords_from_hints(song: SongMetadata) -> SongMetadata:
    """
    Load the chords from the hints folder for the given song.
    file location: "/songs/hints/<song_name>.chords.json"

    Args:
        song (SongMetadata): The song metadata object to load chords into.
    Returns:
        SongMetadata: The updated song metadata object with chords loaded (if exists).
    """
    file_path = f"{song.songs_folder}/hints/{song.song_name}.chords.json"
    try:
        with open(file_path, 'r') as f:
            song.chords = json.load(f)
        logger.info(f" 📖 Chords loaded from {file_path}")
    except FileNotFoundError:
        logger.info(f" ⚠️ Chords file not found [{file_path}]")
        pass
    return song

if __name__ == "__main__":
    # Example usage
    song = SongMetadata(
        song_name="born_slippy",
        songs_folder="/home/darkangel/ai-light-show/songs",
        ignore_existing=True
    )
    # Initialize arrangement if needed
    if not hasattr(song, 'arrangement'):
        song.arrangement = []
    
    # Load arrangement
    song = load_arrangement_from_hints(song)
    print(f"Arrangement loaded: {song.arrangement}")
    
    # Load key moments
    song = load_key_moments_from_hints(song)
    print(f"Key moments loaded: {song.key_moments}")
    
    # Load chords
    song = load_chords_from_hints(song)
    print(f"Chords loaded: {song.chords}")
