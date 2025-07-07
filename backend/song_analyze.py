from backend.ai.pattern_finder_ml import get_stem_clusters_with_model
from backend.models.song_metadata import SongMetadata, Section
from backend.ai.arrangement_guess import guess_arrangement
from backend.ai.essentia_analysis import extract_with_essentia
from backend.ai.drums_infer import infer_drums
from backend.ai.demucs_split import extract_stems
from backend.ai.pattern_finder import get_stem_clusters
from backend.ai.audio_proccess import noise_gate

def song_analyze(song: SongMetadata, reset_file: bool = True) -> SongMetadata:

    """
    Analyze a song and extract its metadata, beats, BPM, and patterns.
    This function uses Essentia for core analysis and Demucs for stem extraction.
    :param song: SongMetadata object containing the song to analyze.
    :param reset_file: If True, will re-create entire metadata.
    :return: Updated SongMetadata object with analysis results.
    """

    analyze_patterns_using_model = False
    infer_drums_using_model = False


    print(f"🔍 Analyzing song: {song.title} ({song.mp3_path})")

    if reset_file:
        song = SongMetadata(song.song_name, songs_folder=song.songs_folder, ignore_existing=True)

    ## Core analysis using Essentia
    essentia_core = extract_with_essentia(song.mp3_path)
    song.clear_beats()
    song.bpm = essentia_core['bpm']
    song.duration = essentia_core['song_duration']
    [song.add_beat(b) for b in essentia_core['beats']]
    song.set_beats_volume(essentia_core['beat_volumes'])

    ## split song into stems
    stems_folder = extract_stems(song.mp3_path)

    # analyze stems
    stems_list = ['drums', 'bass']
    song.clear_patterns()

    for stem in stems_list:
        stem_path = f"{stems_folder['output_folder']}/{stem}.wav"

        # apply noise gate to stem
        noise_gate(input_path=stem_path, threshold_db=-35.0)

        # get clusters (librosa)
        stem_clusters = get_stem_clusters(
            song.get_beats_array(),
            stem_path
        )
        print(f"   → Clusters: {stem_clusters['n_clusters']}")
        print(f"   → Segments: {len(stem_clusters['segments'])}")
        print(f"   → Score: {stem_clusters['clusterization_score']}")
        print(f"  Adding {len(stem_clusters['clusters_timeline'])} clusters for {stem}...")
        song.add_patterns(stem, stem_clusters['clusters_timeline'])

        # get clusters (ML)
        if analyze_patterns_using_model:
            stem_clusters = get_stem_clusters_with_model(
                song.get_beats_array(), 
                stem_path
            )
            song.add_patterns(f"{stem}_m", stem_clusters['clusters_timeline'])

        ## infer drums
        if infer_drums_using_model and stem == 'drums':
            song.drums = infer_drums(stem_path)

    if song.placeholder_prop:
        guess_arrangement(song)

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

    songs_folder="/home/darkangel/ai-light-show/songs"

    # get a list of mp3 files in the songs folder
    import os
    from glob import glob
    mp3_files = glob(os.path.join(songs_folder, "*.mp3"))
    if not mp3_files:
        print("No MP3 files found in the songs folder.")
        exit(1)

    # remove all files that are not mp3 files
    failed_to_remove = []
    for file in os.listdir(songs_folder):
        if not file.endswith(".mp3"):
            file_path = os.path.join(songs_folder, file)
            try:
                os.remove(file_path)
            except Exception as e:
                failed_to_remove.append(file_path)

    if failed_to_remove:
        print("Failed to remove the following files:")
        for file in failed_to_remove:
            print(f"  {file}")

    # remove .meta.json files if they exist
    for meta_file in glob(os.path.join(songs_folder, "*.meta.json")):
        try:
            os.remove(meta_file)
            print(f"Removed existing metadata file: {meta_file}")
        except Exception as e:
            print(f"Error removing {meta_file}: {e}")

    for log_file in glob(os.path.join(songs_folder, "*.log")):
        try:
            os.remove(log_file)
            print(f"Removed existing log file: {log_file}")
        except Exception as e:
            print(f"Error removing {log_file}: {e}")

    for mp3_file in mp3_files:
        song_name = os.path.splitext(os.path.basename(mp3_file))[0]
        print(f"Analyzing song: {song_name} ({mp3_file})")
        
        # Create a SongMetadata instance
        song = SongMetadata(song_name, songs_folder=songs_folder, ignore_existing=True)
        
        # Analyze the song
        song = song_analyze(song)
        
        # Save the song metadata
        song.save()


    # Example usage
    # song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs", ignore_existing=True)
    # print(f"---------------------")
    # song = song_analyze(song)
    # song.save()
