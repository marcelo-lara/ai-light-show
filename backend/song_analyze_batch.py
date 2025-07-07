from backend.models.song_metadata import SongMetadata, Section
from backend.song_analyze import song_analyze
if __name__ == "__main__":

    songs_folder="/home/darkangel/ai-light-show/songs"

    # get a list of mp3 files in the songs folder
    import os
    from glob import glob
    mp3_files = glob(os.path.join(songs_folder, "*.mp3"))
    if not mp3_files:
        print("No MP3 files found in the songs folder.")
        exit(1)

    #remove temp folder if it exists
    temp_folder = os.path.join(songs_folder, "temp/htdemucs/*")
    if os.path.exists(temp_folder):
        print(f"Removing existing temp folder: {temp_folder}")
        try:
            os.rmdir(temp_folder)
        except Exception as e:
            print(f"Failed to remove temp folder: {e}")
            exit(1)

    # remove all files that are not mp3 files
    failed_to_remove = []
    for file in os.listdir(songs_folder):
        file_path = os.path.join(songs_folder, file)
        if os.path.isdir(file_path):
            continue  # Skip directories
        if os.path.isdir(file_path) or not file.endswith(".mp3"):
            try:
                os.remove(file_path)
            except Exception as e:
                failed_to_remove.append(file_path)

    if failed_to_remove:
        print("Failed to remove the following files:")
        for file in failed_to_remove:
            print(f"  {file}")
        exit(1)

    for mp3_file in sorted(mp3_files):
        print("\n-----------------------------------------------------------------------")
        song_name = os.path.splitext(os.path.basename(mp3_file))[0]
        print(f"Analyzing song: {song_name} ({mp3_file})")
        
        # Create a SongMetadata instance
        song = SongMetadata(song_name, songs_folder=songs_folder, ignore_existing=True)
        
        # Analyze the song
        song = song_analyze(song)
        
        # Save the song metadata
        song.save()
