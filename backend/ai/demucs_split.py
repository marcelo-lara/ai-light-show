SONGS_TEMP_DIR = "/app/static/songs/temp"
SONGS_FOLDER = "/app/static/songs"

def set_folders(temp_dir:str = '', songs_folder:str =''):
    global SONGS_TEMP_DIR, SONGS_FOLDER
    if not temp_dir == '':
        SONGS_TEMP_DIR = temp_dir
    if not songs_folder == '':
        SONGS_FOLDER = songs_folder

def extract_vocals(input_file: str, output_file: str = '', song_prefix: str = ''):
    """
    Extract vocals from an audio file using Demucs.
    :param input_file: Path to the input audio file.
    :param output_file: Path to save the extracted vocals.
    """
    if song_prefix == '':
        song_prefix = input_file.split("/")[-1].split(".")[0]

    import subprocess
    command = [
        "python", "-m", "demucs.separate", 
        "--two-stems=vocals", 
        "-o", SONGS_TEMP_DIR,
        input_file        
    ]
    
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    print(f"{result.stdout}")

    out_vocal = f"{SONGS_TEMP_DIR}/htdemucs/{song_prefix}/vocals.wav"
    out_no_vocal = f"{SONGS_TEMP_DIR}/htdemucs/{song_prefix}/no_vocals.wav"
    return {
        "vocals": out_vocal,
        "no_vocals": out_no_vocal
    }

def extract_drums(input_file: str, output_file: str = '', song_prefix: str = ''):
    """
    Extract drums from an audio file using Demucs.
    :param input_file: Path to the input audio file.
    :param output_file: Path to save the extracted drums.
    """
    if song_prefix == '':
        song_prefix = input_file.split("/")[-1].split(".")[0]

    import subprocess
    command = [
        "python", "-m", "demucs.separate", 
        "--two-stems=drums", 
        "-o", SONGS_TEMP_DIR,
        input_file        
    ]
    
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    print(f"{result.stdout}")

    out_drum = f"{SONGS_TEMP_DIR}/htdemucs/{song_name}/drums.wav"
    out_no_drum = f"{SONGS_TEMP_DIR}/htdemucs/{song_name}/no_drums.wav"
    return {
        "drums": out_drum,
        "no_drums": out_no_drum
    }

## Example usage:
if __name__ == "__main__":
    set_folders(
        temp_dir="/home/darkangel/ai-light-show/songs/temp", 
        songs_folder="/home/darkangel/ai-light-show/songs"
      )
    songs_file = "/home/darkangel/ai-light-show/songs/born_slippy.mp3"
    song_name = songs_file.split("/")[-1].split(".")[0]

    print(f"Extracting drums from {songs_file}...")
    results = extract_drums(songs_file)

    print(f"Drums extracted to {results['drums']}")
    print(f"No drums extracted to {results['no_drums']}")   
    print("-----------")

    print(f"Extracting vocals from {songs_file}...")
    results = extract_vocals(songs_file)
    print(f"Vocals extracted to {results['vocals']}")
    print(f"No vocals extracted to {results['no_vocals']}")
    print("-----------")