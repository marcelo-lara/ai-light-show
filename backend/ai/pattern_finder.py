import numpy as np
import librosa
import soundfile as sf
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from scipy.cluster.hierarchy import linkage
from kneed import KneeLocator
from pathlib import Path
from collections import Counter

def get_suggested_threshold(features, step=1):
    features_sampled = features[::step]
    Z = linkage(features_sampled, method='ward')
    merge_distances = Z[:, 2]
    x = np.arange(len(merge_distances))
    knee = KneeLocator(x, merge_distances, curve='convex', direction='increasing')
    return merge_distances[knee.knee] if knee.knee is not None else 20.0

def get_stem_clusters(beats, stem_file, full_file=None, n_mels=64, fmax=8000, hop_length=512,
                      min_duration_beats=1, debug=False):
    """
    Analyze a stem file to identify repeating audio patterns across beat-aligned segments.

    Args:
        beats (np.ndarray): Array of beat timestamps in seconds.
        stem_file (str): Path to the isolated stem (.wav).
        full_file (str, optional): Path to the full mix source file.
        n_mels (int): Number of Mel bands to use.
        fmax (int): Max frequency for mel spectrogram.
        hop_length (int): Hop size for feature extraction.
        min_duration_beats (int): Minimum length of segment (in beats) to consider.
        debug (bool): Whether to export sample .wav for each cluster.

    Returns:
        dict: {
            'cluster_labels': list of ints,
            'segments': list of (start_time, end_time),
            'n_clusters': int
        }
    """
    # Input validation
    if len(beats) < min_duration_beats + 1:
        raise ValueError(f"Not enough beats ({len(beats)}) for minimum segment duration ({min_duration_beats})")
    
    if not Path(stem_file).exists():
        raise FileNotFoundError(f"Stem file not found: {stem_file}")

    print(f"𝍇 Analyzing clusters of {stem_file}")

    y, sr = librosa.load(stem_file, sr=None)
    
    if len(y) == 0:
        raise ValueError("Audio file is empty or could not be loaded")

    # Build beat-aligned segments
    segments = []
    for i in range(len(beats) - min_duration_beats):
        start_time = beats[i]
        end_time = beats[i + min_duration_beats]
        segments.append((start_time, end_time))

    # Extract richer features per segment
    segment_features = []
    silence_indices = []
    
    # First pass: calculate feature dimensions from a non-silent segment
    feature_dim = None
    for idx, (start, end) in enumerate(segments):
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        segment_audio = y[start_sample:end_sample]
        
        if not np.allclose(segment_audio, 0, atol=1e-4):
            S = librosa.feature.melspectrogram(y=segment_audio, sr=sr, n_mels=n_mels, fmax=fmax)
            log_S = librosa.power_to_db(S, ref=np.max)
            mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
            chroma = librosa.feature.chroma_stft(S=S, sr=sr)
            rms = librosa.feature.rms(y=segment_audio)
            
            feature_vector = np.hstack([
                np.mean(log_S, axis=1),
                np.std(log_S, axis=1),
                np.mean(mfcc, axis=1),
                np.mean(chroma, axis=1),
                np.mean(rms)
            ])
            feature_dim = len(feature_vector)
            break
    
    # If all segments are silent, use default feature dimension
    if feature_dim is None:
        feature_dim = n_mels * 2 + 13 + 12 + 1  # mel_mean + mel_std + mfcc + chroma + rms
    
    # Second pass: extract features with consistent dimensions
    for idx, (start, end) in enumerate(segments):
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        segment_audio = y[start_sample:end_sample]

        if np.allclose(segment_audio, 0, atol=1e-4):
            silence_indices.append(idx)
            segment_features.append(np.zeros(feature_dim))
            continue

        S = librosa.feature.melspectrogram(y=segment_audio, sr=sr, n_mels=n_mels, fmax=fmax)
        log_S = librosa.power_to_db(S, ref=np.max)
        mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
        chroma = librosa.feature.chroma_stft(S=S, sr=sr)
        rms = librosa.feature.rms(y=segment_audio)

        feature_vector = np.hstack([
            np.mean(log_S, axis=1),
            np.std(log_S, axis=1),
            np.mean(mfcc, axis=1),
            np.mean(chroma, axis=1),
            np.mean(rms)
        ])
        segment_features.append(feature_vector)

    X = np.array(segment_features)
    X = StandardScaler().fit_transform(X)
    
    # Dimensionality reduction using PCA
    n_components = min(10, X.shape[1], X.shape[0]-1)
    if n_components > 0:
        X_reduced = PCA(n_components=n_components).fit_transform(X)
    else:
        X_reduced = X

    # Determine optimal threshold
    threshold = get_suggested_threshold(X_reduced)

    # Cluster segments
    clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold, linkage='ward')
    raw_labels = clustering.fit_predict(X_reduced)

    # Handle silence segments and label remapping more robustly
    cluster_labels = raw_labels.copy()
    
    # If there are silence segments, assign them to cluster 0 and shift others
    if silence_indices:
        # Find unique non-silence labels
        non_silence_labels = set(raw_labels[i] for i in range(len(raw_labels)) if i not in silence_indices)
        
        # Create label mapping: silence -> 0, others -> 1, 2, 3, ...
        label_map = {}
        next_label = 1
        for label in sorted(non_silence_labels):
            label_map[label] = next_label
            next_label += 1
        
        # Apply the mapping
        for i in range(len(cluster_labels)):
            if i in silence_indices:
                cluster_labels[i] = 0
            else:
                cluster_labels[i] = label_map[raw_labels[i]]
    # If no silence, just ensure labels start from 0
    else:
        unique_labels = sorted(set(raw_labels))
        label_map = {old: new for new, old in enumerate(unique_labels)}
        cluster_labels = [label_map[label] for label in raw_labels]

    # Save a debug audio snippet per cluster
    if debug:
        output_base = Path(stem_file).with_suffix("")
        exported = set()
        print("Cluster Distribution:")
        label_counts_temp = Counter(cluster_labels)
        total = sum(label_counts_temp.values())
        for label, count in sorted(label_counts_temp.items()):
            bar = '█' * int((count / total) * 50)
            print(f"Cluster {label:2d}: {count:3d} segments | {bar}")

        for i, label in enumerate(cluster_labels):
            if label in exported:
                continue
            exported.add(label)
            start, end = segments[i]
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            segment_audio = y[start_sample:end_sample]
            temp_wav = output_base.parent / f"{output_base.stem}_cluster{label}.wav"
            sf.write(temp_wav, segment_audio, sr)
    label_counts = Counter(cluster_labels)
    segment_times_by_cluster = {}
    for i, label in enumerate(cluster_labels):
        segment_times_by_cluster.setdefault(label, []).append(segments[i])

    return {
        "cluster_labels": cluster_labels if isinstance(cluster_labels, list) else cluster_labels.tolist(),
        "segments": segments,
        "clusters_timeline": [
            {
                "start": start,
                "end": end,
                "segmentId": cluster
            }
            for (start, end), cluster in sorted(zip(segments, cluster_labels), key=lambda x: x[0][0])
        ],
        "n_clusters": int(len(set(cluster_labels))),
        "cluster_counts": dict(label_counts),
        "segment_times_by_cluster": segment_times_by_cluster
    }

## Example usage:
if __name__ == "__main__":

    # get base parameters
    from backend.song_metadata import SongMetadata
    song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs")

    beats = song.get_beats_array()

    stem_file = f"/home/darkangel/ai-light-show/songs/temp/htdemucs/{song.song_name}/drums.wav"
    print(f"Clustering {stem_file}...")

    stem_clusters = get_stem_clusters(beats, stem_file, full_file=song.mp3_path, debug=True)

    song.add_patterns("drums", stem_clusters['clusters_timeline'])
    song.save()

    #todo: save as json
    import json
    with open(f"/home/darkangel/ai-light-show/songs/temp/htdemucs/{song.song_name}/stem_clusters.json", "w") as f:
        json.dump(stem_clusters, f, indent=4)

    print(f"Found {stem_clusters['n_clusters']} clusters in the stem.")
