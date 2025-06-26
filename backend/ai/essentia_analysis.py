import essentia
import essentia.standard as es
import json
from pathlib import Path
from backend.config import LOCAL_TEST_SONG_PATH
from sklearn.cluster import KMeans
import numpy as np

def extract_beats_and_chords(audio_path: str, output_json_path: str = '', bars_1=4, bars_2=2):
    if output_json_path == '':
        output_json_path = audio_path + ".beats_chords.json"

    # Load audio (mono)
    loader = es.MonoLoader(filename=audio_path)
    audio = loader()

    # Beat detection
    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    bpm, beats, _, _, _ = rhythm_extractor(audio)

    # Chroma extraction (via HPCP)
    frame_size = 4096
    hop_size = 2048

    windowing = es.Windowing(type='hann')
    spectrum = es.Spectrum()
    spectral_peaks = es.SpectralPeaks()
    hpcp_extractor = es.HPCP(size=12)

    hpcp_time_series = []
    audio_duration = len(audio) / 44100.0
    frame_times = []

    for i, frame in enumerate(es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size, startFromZero=True)): 
        timestamp = (i * hop_size) / 44100.0
        spec = spectrum(windowing(frame))
        freqs, mags = spectral_peaks(spec)
        hpcp = hpcp_extractor(freqs, mags)
        hpcp_time_series.append([float(h) for h in hpcp])
        frame_times.append(timestamp)

    # Key detection
    key_detector = es.KeyExtractor()
    key, scale, strength = key_detector(audio)

    # Helper to average HPCP vectors over a time range
    def get_avg_hpcp(start, end):
        values = [vec for t, vec in zip(frame_times, hpcp_time_series) if start <= t < end]
        if not values:
            return [0.0] * 12
        return [float(sum(col) / len(col)) for col in zip(*values)]

    # Generate bar-based regions
    bar_duration_sec = (60.0 / bpm) * 4
    beats_sec = [float(b) for b in beats]
    song_duration = beats_sec[-1] if beats_sec else audio_duration

    def generate_regions(bars):
        duration = (60.0 / bpm) * bars
        t = 0.0
        regions = []
        while t < song_duration:
            end = t + duration
            hpcp = get_avg_hpcp(t, end)
            energy = sum(hpcp)  # crude energy metric
            regions.append({
                "start": round(t, 3),
                "end": round(end, 3),
                "hpcp": [round(val, 4) for val in hpcp],
                "energy": round(energy, 4)
            })
            t = end
        return regions

    def cluster_regions(regions, n_clusters=4):
        X = np.array([r["hpcp"] for r in regions])
        if len(X) < n_clusters:
            return regions
        kmeans = KMeans(n_clusters=n_clusters, random_state=0, n_init=10).fit(X)
        for i, r in enumerate(regions):
            r["label"] = chr(65 + kmeans.labels_[i])  # 'A', 'B', 'C', ...
        return regions

    regions_4 = cluster_regions(generate_regions(bars_1))
    regions_2 = cluster_regions(generate_regions(bars_2))

    avg_hpcp = get_avg_hpcp(0.0, song_duration)

    # Save result
    results = {
        "bpm": round(float(bpm), 2),
        "beats": [round(float(b), 4) for b in beats],
        "key": key,
        "scale": scale,
        "strength": float(strength),
        "avg_hpcp": [round(float(val), 4) for val in avg_hpcp],
        "regions_4bars": regions_4,
        "regions_2bars": regions_2
    }

    Path(output_json_path).write_text(json.dumps(results, indent=2))
    print(f"✅ Saved beat and chord data to {output_json_path}")
    return results


if __name__ == "__main__":
    extract_beats_and_chords(
        LOCAL_TEST_SONG_PATH,
        LOCAL_TEST_SONG_PATH + ".beats_chords.json"
    )
