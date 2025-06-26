import librosa
import json

song_beats = []

def get_song_beats(song_path: str) -> list[float]:
    global song_beats
    if not song_beats:
        song_beats = extract_beats(song_path, song_path + ".beats.json")
    return song_beats

def extract_beats(audio_path: str, output_path: str):
    y, sr = librosa.load(audio_path)
    # Use only the percussive component for beat tracking
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    tempo, beat_frames = librosa.beat.beat_track(y=y_percussive, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    beat_times = [round(t, 4) for t in beat_times]

    print(f"✅ Detected {len(beat_times)} beats at ~{float(tempo):.2f} BPM")

    with open(output_path, "w") as f:
        json.dump(beat_times, f, indent=2)
    
    return beat_times
