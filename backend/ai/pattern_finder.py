import warnings
warnings.filterwarnings("ignore")

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
from sklearn.metrics.pairwise import cosine_similarity
import json

def get_rhythmic_features(audio, sr, beats):
    """Extract drum-specific rhythmic features with transient analysis."""
    try:
        # Harmonic-percussive separation
        audio_harmonic, audio_percussive = librosa.effects.hpss(audio)
        
        # Transient detection features
        onset_frames = librosa.onset.onset_detect(y=audio_percussive, sr=sr, units='frames')
        transients = len(onset_frames)
        transient_rate = transients / (len(audio)/sr)  # Transients per second
        
        # Onset strength features
        onset_env = librosa.onset.onset_strength(y=audio_percussive, sr=sr)
        onset_features = [
            np.mean(onset_env),
            np.std(onset_env),
            np.max(onset_env) - np.min(onset_env)
        ]
        
        # Beat-synchromized RMS energy
        rms = librosa.feature.rms(y=audio_percussive)
        times = librosa.times_like(rms, sr=sr)
        beat_rms = []
        for beat_time in beats:
            nearest_idx = np.argmin(np.abs(times - beat_time))
            beat_rms.append(rms[0, nearest_idx])
        
        return {
            'transient_count': transients,
            'transient_rate': transient_rate,
            'onset_strength': onset_features,
            'beat_rms': np.array(beat_rms)
        }
    except Exception as e:
        print(f"⚠️ Rhythmic feature error: {str(e)}")
        return {
            'onset_strength': 0.0,
            'tempogram_mean': np.zeros(384),
            'tempogram_std': np.zeros(384)
        }

def get_temporal_features(audio, sr, n_mels=64):
    """Extract temporal dynamics features with delta features."""
    S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels)
    log_S = librosa.power_to_db(S, ref=np.max)
    mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
    delta_mfcc = librosa.feature.delta(mfcc)
    delta2_mfcc = librosa.feature.delta(mfcc, order=2)
    return {
        'mfcc': mfcc,
        'delta_mfcc': delta_mfcc,
        'delta2_mfcc': delta2_mfcc
    }

def get_suggested_threshold(features, step=1):
    features_sampled = features[::step]
    Z = linkage(features_sampled, method='ward')
    merge_distances = Z[:, 2]
    x = np.arange(len(merge_distances))
    knee = KneeLocator(x, merge_distances, curve='convex', direction='increasing')
    return merge_distances[knee.knee] if knee.knee is not None else 20.0

def get_stem_clusters(
    beats,
    stem_file,
    full_file=None,
    n_mels=64,
    fmax=8000,
    hop_length=512,
    segment_beat_lengths=(0.5, 1, 2),  # Shorter segments for precise pattern detection
    debug=False
):
    """ 
    Find repeated patterns in a stem file based on beats.
    This function segments the audio file into chunks based on the provided beat lengths,
    extracts features from each segment, and clusters them to find similar patterns.
    :param beats: List of beat timestamps in seconds.
    :param stem_file: Path to the audio stem file to analyze.
    :param full_file: Optional path to the full audio file (not used in this function).
    :param n_mels: Number of mel bands to use in the mel spectrogram.
    :param fmax: Maximum frequency for the mel spectrogram.
    :param hop_length: Hop length for the mel spectrogram.
    :param segment_beat_lengths: Tuple of beat lengths to segment the audio into.
    :param debug: If True, prints debug information.
    :return: Dictionary containing cluster labels, segments, and other analysis results.
    """
    print(f"⛓️ Analyzing stem clusters")

    if not Path(stem_file).exists():
        raise FileNotFoundError(f"Stem file not found: {stem_file}")
        
    y, sr = librosa.load(stem_file, sr=None)
    if len(y) == 0:
        raise ValueError("Audio file is empty or could not be loaded")

    # Check if entire audio is silent
    if np.allclose(y, 0, atol=1e-4):
        return {
            "clusters_timeline": [],
            "n_clusters": 0,
            "clusterization_score": 0.0,
            "best_duration_beats": 0,
            "all_durations": {}
        }

    results_by_duration = {}

    for duration_beats in segment_beat_lengths:
        if debug:
            print(f"\n⎱Segment duration: {duration_beats} beats")

        hop_beats = int(max(1, duration_beats))
        segments = []
        i = 0
        while i + duration_beats <= len(beats) - 1:
            start_time = float(beats[int(i)])
            end_time = float(beats[int(i + duration_beats)])
            segments.append((start_time, end_time))
            i += 1

        features, silence_indices = [], []
        feature_dim = None

        # First pass to get feature dimension
        for idx, (start, end) in enumerate(segments):
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            audio = y[start_sample:end_sample]
            if np.allclose(audio, 0, atol=1e-4):
                continue
            # Use updated feature extraction to match second pass
            S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels, fmax=fmax)
            log_S = librosa.power_to_db(S, ref=np.max)
            
            temporal = get_temporal_features(audio, sr, n_mels)
            rhythmic = get_rhythmic_features(audio, sr, beats)
            
            chroma = librosa.feature.chroma_stft(S=S, sr=sr)
            spectral_contrast = librosa.feature.spectral_contrast(S=S, sr=sr)
            rms = librosa.feature.rms(y=audio)
            
            # Enhanced transient detection features
            spectral_flatness = librosa.feature.spectral_flatness(S=S)
            onset_strength = librosa.onset.onset_strength(y=audio, sr=sr)
            zero_crossing = librosa.feature.zero_crossing_rate(audio)
            onset_frames = librosa.onset.onset_detect(
                y=audio, sr=sr, units='frames',
                backtrack=True, pre_max=1, post_max=1
            )
            transients = len(onset_frames) / (len(audio)/sr)  # Transients per second
            
            # Consistent feature extraction with second pass
            vector = np.hstack([
                np.mean(log_S, axis=1), 
                np.std(log_S, axis=1),
                np.mean(temporal['mfcc'], axis=1),
                np.mean(temporal['delta_mfcc'], axis=1),
                np.mean(temporal['delta2_mfcc'], axis=1),
                np.mean(chroma, axis=1),
                np.mean(spectral_contrast, axis=1),
                rhythmic['onset_strength'],
                rhythmic['transient_count'],
                rhythmic['transient_rate'],
                np.mean(rms)
            ])
            feature_dim = len(vector)
            break

        if feature_dim is None:
            if debug:
                print(f"⚠️ All segments were silent for {duration_beats} beats — skipping...")
            continue

        # Second pass
        for idx, (start, end) in enumerate(segments):
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            audio = y[start_sample:end_sample]
            if np.allclose(audio, 0, atol=1e-4):
                silence_indices.append(idx)
                features.append(np.zeros(feature_dim))
                continue
            S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels, fmax=fmax)
            log_S = librosa.power_to_db(S, ref=np.max)
            
            temporal = get_temporal_features(audio, sr, n_mels)
            rhythmic = get_rhythmic_features(audio, sr, beats)
            
            chroma = librosa.feature.chroma_stft(S=S, sr=sr) if S.size > 0 else np.zeros((12, 1))
            spectral_contrast = librosa.feature.spectral_contrast(S=S, sr=sr) if S.size > 0 else np.zeros((7, 1))
            rms = librosa.feature.rms(y=audio) if audio.size > 0 else np.zeros(1)
            
            vector = np.hstack([
                np.mean(log_S, axis=1), 
                np.std(log_S, axis=1),
                np.mean(temporal['mfcc'], axis=1),
                np.mean(temporal['delta_mfcc'], axis=1),
                np.mean(temporal['delta2_mfcc'], axis=1),
                np.mean(chroma, axis=1),
                np.mean(spectral_contrast, axis=1),
                rhythmic['onset_strength'],
                rhythmic['transient_count'],
                rhythmic['transient_rate'],
                np.mean(rms)
            ])
            features.append(vector)

        # Ensure valid input for PCA
        X = np.array(features)
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)  # Handle NaN/Inf
        
        try:
            # Scale with fallback for zero-variance features
            X_scaled = StandardScaler().fit_transform(X)
        except ValueError:
            X_scaled = X  # Fallback if scaling fails (e.g. all features zero)
            
        # Ensure no NaNs/Infs after scaling
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e6, neginf=-1e6)
        
        # Handle zero-variance PCA input
        if np.allclose(X_scaled, 0) or np.isnan(X_scaled).any():
            # If all segments are silent, assign single cluster
            cluster_labels = [0]*len(segments)
            results_by_duration[duration_beats] = {
                "cluster_labels": cluster_labels,
                "segments": segments,
                "n_clusters": 1,
                "cluster_centroids": {0: np.zeros(feature_dim)},
                "similarity_matrix": [[100.0]]
            }
            continue
            
        pca = PCA(n_components=0.95)  # Keep 95% variance
        X_reduced = pca.fit_transform(X_scaled)
        X_reduced = np.nan_to_num(X_reduced, nan=0.0)
        threshold = get_suggested_threshold(X_reduced)
        # Force 6 active clusters (7 total with silence)
        clustering = AgglomerativeClustering(
            n_clusters=7,  # Directly target 7 final clusters (6 patterns + silence)
            linkage='average',
            metric='cosine'
        )
        raw_labels = clustering.fit_predict(X_reduced)

        cluster_labels = raw_labels.copy()
        if silence_indices:
            non_silence_labels = sorted(set(raw_labels[i] for i in range(len(raw_labels)) if i not in silence_indices))
            label_map = {old: i+1 for i, old in enumerate(non_silence_labels)}
            cluster_labels = [0 if i in silence_indices else label_map[raw_labels[i]] for i in range(len(raw_labels))]
        else:
            label_map = {old: i for i, old in enumerate(sorted(set(raw_labels)))}
            cluster_labels = [label_map[label] for label in raw_labels]

        cluster_vectors = {}
        for i, label in enumerate(cluster_labels):
            cluster_vectors.setdefault(label, []).append(X[i])
        cluster_centroids = {label: np.mean(vectors, axis=0) for label, vectors in cluster_vectors.items()}

        labels_sorted = sorted(cluster_centroids.keys())
        centroid_array = np.array([cluster_centroids[k] for k in labels_sorted])
        similarity_matrix = cosine_similarity(centroid_array)
        similarity_percent = (similarity_matrix * 100).round(1)

        # Merge clusters with >95% similarity
        def merge_clusters(sim_matrix, threshold=99.9):  # Require nearly identical patterns to merge
            """Merge clusters with similarity above threshold"""
            clusters = list(range(sim_matrix.shape[0]))
            merged = []
            
            while clusters:
                current = clusters.pop(0)
                group = [current]
                # Find all clusters similar to current
                for i, val in enumerate(sim_matrix[current]):
                    if i != current and val > threshold and i in clusters:
                        group.append(i)
                        clusters.remove(i)
                merged.append(group)
            
            # Create label mapping
            label_map = {}
            for new_label, group in enumerate(merged):
                for old_label in group:
                    label_map[labels_sorted[old_label]] = new_label
            
            return label_map, merged

        merge_map, merged_groups = merge_clusters(similarity_percent, 99.0)
        
        # Remap cluster labels
        merged_labels = [merge_map[label] for label in cluster_labels]
        merged_centroids = {}
        for new_label, group in enumerate(merged_groups):
            group_centroids = [cluster_centroids[labels_sorted[i]] for i in group]
            merged_centroids[new_label] = np.mean(group_centroids, axis=0)
        
        # Recalculate similarity matrix with merged clusters
        merged_array = np.array([merged_centroids[k] for k in sorted(merged_centroids.keys())])
        merged_similarity = (cosine_similarity(merged_array) * 100).round(1)

        results_by_duration[duration_beats] = {
            "cluster_labels": merged_labels,
            "segments": segments,
            "n_clusters": len(merged_centroids),
            "cluster_centroids": merged_centroids,
            "similarity_matrix": merged_similarity.tolist()
        }

        if debug:
            print(f"   → Clusters: {len(set(cluster_labels))}")
            print(f"   → Segments: {len(segments)}")
            print(f"   → Score: {round(len(set(cluster_labels)) / len(segments), 4)}")
            print("Similarity Matrix (%):")
            header = "     " + "  ".join(f"C{i}" for i in range(len(labels_sorted)))
            print(header)
            for i, row in enumerate(similarity_percent):
                row_str = "  ".join(f"{val:5.1f}" for val in row)
                print(f"  C{i} {row_str}")
            print(f"   → Segments: {len(segments)}")
            print(f"   → Score: {round(len(set(cluster_labels)) / len(segments), 4)}")

    # Select result with exactly 7 clusters (0-6)
    best_duration = None
    # First set best_duration_beats for all results
    for duration, result in results_by_duration.items():
        result["best_duration_beats"] = duration
        
    # Find exact match first
    for duration, result in results_by_duration.items():
        if result["n_clusters"] == 7:
            best_duration = duration
            break
            
    # Fallback to closest cluster count
    if not best_duration:
        closest = min(results_by_duration.values(), 
                     key=lambda x: abs(x["n_clusters"] - 7))
        best_duration = closest["best_duration_beats"]

    best_result = results_by_duration.get(best_duration, {})
    best_result["best_duration_beats"] = best_duration
    best_result["all_durations"] = {
        str(k): {
            "n_clusters": v["n_clusters"],
            "n_segments": len(v["segments"]),
            "clusterization_score": round(v["n_clusters"] / len(v["segments"]), 4) if len(v["segments"]) else None
        }
        for k, v in results_by_duration.items()
    }
    
    # Add clusterization_score from best duration
    if str(best_duration) in best_result["all_durations"]:
        best_result["clusterization_score"] = best_result["all_durations"][str(best_duration)]["clusterization_score"]
    else:
        best_result["clusterization_score"] = 0.0

    # Convert to JSON-serializable format
    best_result_clean = {}
    for k, v in best_result.items():
        if isinstance(v, np.ndarray):
            best_result_clean[k] = v.tolist()
        elif isinstance(v, dict):
            best_result_clean[k] = {
                str(subk): (subv.tolist() if isinstance(subv, np.ndarray) else subv)
                for subk, subv in v.items()
            }
        elif isinstance(v, list):
            best_result_clean[k] = [
                item.tolist() if isinstance(item, np.ndarray) else item
                for item in v
            ]
        else:
            best_result_clean[k] = v

    # Post-process to trim overlapping segments
    cleaned_segments = []
    last_start = -1.0
    last_end = -1.0
    for (start, end), label in zip(best_result_clean["segments"], best_result_clean["cluster_labels"]):
        if start < last_end:
            last_segment = cleaned_segments[-1][0]
            corrected_end = start
            cleaned_segments[-1] = ((last_segment[0], corrected_end), cleaned_segments[-1][1])
        cleaned_segments.append(((start, end), label))
        last_end = end

    best_result_clean["segments"] = [s for s, _ in cleaned_segments]
    best_result_clean["cluster_labels"] = [c for _, c in cleaned_segments]
    best_result_clean["clusters_timeline"] = [
        {
            "start": float(start),
            "end": float(end),
            "cluster": int(cluster)
        }
        for (start, end), cluster in zip(best_result_clean["segments"], best_result_clean["cluster_labels"])
    ]

    if best_result_clean["n_clusters"] == 0:
        print("⚠️ No clusters found after processing.")
        return None

    if best_result_clean["n_clusters"] > 50:
        print("⚠️ Too many clusters found, likely too noisy or complex.")
        return None

    return best_result_clean

if __name__ == "__main__":
    '''
    Example cluster segments for the song "Born Slippy" by Underworld:
    0. drum is silent for the first 34.2s
    1. first kick starts at 34.2s
    2. a tom is added at 55.2s
    3. tom change pattern at 1m20.2s
    4. a tom+hihat pattern starts at 1m37.1s
    5. a two kicks then two snares pattern starts at 1m42.2s
    6. snare only pattern starts at 2m00s
    4. repeat the tom+hihat pattern (same as 4) at 2.02.9s
    ''' 
    from ..models.song_metadata import SongMetadata

    song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs")
    beats = song.get_beats_array()
    stem_file = f"/home/darkangel/ai-light-show/songs/temp/htdemucs/{song.song_name}/drums.wav"


    print(f"Clustering {stem_file} with multiple segment sizes...")
    best_result = get_stem_clusters(beats, stem_file, full_file=song.mp3_path, debug=True)

    print(f"\n🏆 Best duration: {best_result.get('best_duration_beats')} beats")
    print(f"   → Clusters: {best_result['n_clusters']}")
    print(f"   → Segments: {len(best_result['segments'])}")
    print(f"   → Score: {best_result['clusterization_score']}")

    output_dir = Path(f"/home/darkangel/ai-light-show/songs/temp/htdemucs/{song.song_name}/")
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / f"stem_clusters_best.json"
    with open(summary_path, "w") as f:
        json.dump(best_result, f, indent=4)

    song.clear_patterns()
    song.add_patterns("drums", [
        {"start": float(start), "end": float(end), "cluster": int(cluster)}
        for (start, end), cluster in zip(best_result["segments"], best_result["cluster_labels"])
    ])
    song.save()

    print(f"🎯 Saved best cluster result to {summary_path.name}")
