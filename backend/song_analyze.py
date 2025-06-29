from backend.song_metadata import SongMetadata
from backend.ai.essentia_analysis import extract_with_essentia

def song_analyze(song: SongMetadata) -> SongMetadata:
    print(f"🔍 Analyzing song: {song.title} ({song.mp3_path})")

    ## Core analysis using Essentia
    essentia_core = extract_with_essentia(song.mp3_path)
    song.clear_beats()
    song.bpm = essentia_core['bpm']
    song.duration = essentia_core['song_duration']
    [song.add_beat(b) for b in essentia_core['beats']]
    song.set_beats_volume(essentia_core['beat_volumes'])

    return song

def build_test_cues(song: SongMetadata) -> list:
    """
    Build cues for all beats in the song.
    A flash preset is assigned cycling through fixtures.
    The start_brightness is set proportional to the beat volume.
    """
    fixtures_id = ["parcan_pl", "parcan_pr", "parcan_l", "parcan_r"]
    cues = []
    current_fixture = 0
    for beat in song.beats:
        cues.append(add_flash_preset(
            start_time=beat["time"],
            fixture=fixtures_id[current_fixture],
            start_brightness=beat["volume"]
        ))
        current_fixture += 1
        if current_fixture >= len(fixtures_id):
            current_fixture = 0
    return cues

def add_flash_preset(start_time:float=0.0, fixture:str="parcan_l", start_brightness:float=1.0) -> dict:
    """
    Returns a dictionary of fixture presets.
    This is a placeholder function that should be replaced with actual fixture preset loading logic.
    """
    return  {
        "time": start_time,
        "fixture": fixture,
        "preset": "flash",
        "parameters": {
            "fade_beats": 1,
            "start_brightness": start_brightness
        },
        "duration": 1,
        "chaser": "ai",
        "chaser_id": "ai_generated_000"
    }


if __name__ == "__main__":
    # Example usage
    song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
    song = song_analyze(song)
    song.save()
