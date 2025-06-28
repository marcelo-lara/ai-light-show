from backend.song_metadata import SongMetadata
from backend.ai.essentia_analysis import extract_with_essentia

def song_analyze(song: SongMetadata) -> SongMetadata:
    print(f":: Analyzing song: {song.title} ({song.mp3_path})")

    ## Core analysis using Essentia
    essentia_core = extract_with_essentia(song.mp3_path)
    song.clear_beats()
    song.bpm = essentia_core['bpm']
    song.duration = essentia_core['song_duration']
    [song.add_beat(b) for b in essentia_core['beats']]
    song.set_beats_volume(essentia_core['beat_volumes'])

    return song

if __name__ == "__main__":
    # Example usage
    song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
    song = song_analyze(song)
    song.save()
