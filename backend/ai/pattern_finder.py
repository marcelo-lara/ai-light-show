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
    segment_beat_lengths=(0.5, 1, 2, 4),
    debug=False
):
    if not Path(stem_file).exists():
        raise FileNotFoundError(f"Stem file not found: {stem_file}")
    y, sr = librosa.load(stem_file, sr=None)
    if len(y) == 0:
        raise ValueError("Audio file is empty or could not be loaded")

    results_by_duration = {}

    for duration_beats in segment_beat_lengths:
        if debug:
            print(f"\n⎱ Segment duration: {duration_beats} beats")

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
            S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels, fmax=fmax)
            log_S = librosa.power_to_db(S, ref=np.max)
            mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
            chroma = librosa.feature.chroma_stft(S=S, sr=sr)
            rms = librosa.feature.rms(y=audio)
            vector = np.hstack([
                np.mean(log_S, axis=1), np.std(log_S, axis=1),
                np.mean(mfcc, axis=1), np.mean(chroma, axis=1),
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
            mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
            chroma = librosa.feature.chroma_stft(S=S, sr=sr)
            rms = librosa.feature.rms(y=audio)
            vector = np.hstack([
                np.mean(log_S, axis=1), np.std(log_S, axis=1),
                np.mean(mfcc, axis=1), np.mean(chroma, axis=1),
                np.mean(rms)
            ])
            features.append(vector)

        X = StandardScaler().fit_transform(features)
        X_reduced = PCA(n_components=min(10, X.shape[1], X.shape[0]-1)).fit_transform(X)
        threshold = get_suggested_threshold(X_reduced)
        clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=threshold, linkage='ward')
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

        results_by_duration[duration_beats] = {
            "cluster_labels": cluster_labels,
            "segments": segments,
            "n_clusters": len(set(cluster_labels)),
            "cluster_centroids": cluster_centroids,
            "similarity_matrix": similarity_percent.tolist(),
        }

        if debug:
            print(f"   → Clusters: {len(set(cluster_labels))}")
            print(f"   → Segments: {len(segments)}")
            print(f"   → Score: {round(len(set(cluster_labels)) / len(segments), 4)}")
            print("   → Similarity Matrix (%):")
            header = "     " + "  ".join(f"C{i}" for i in range(len(labels_sorted)))
            print(header)
            for i, row in enumerate(similarity_percent):
                row_str = "  ".join(f"{val:5.1f}" for val in row)
                print(f"  C{i} {row_str}")
            print(f"   → Segments: {len(segments)}")
            print(f"   → Score: {round(len(set(cluster_labels)) / len(segments), 4)}")

    # Select best result based on lowest n_clusters / segments ratio
    best_duration = None
    best_score = float('inf')
    for duration, result in results_by_duration.items():
        num_clusters = result["n_clusters"]
        num_segments = len(result["segments"])
        if num_segments == 0:
            continue
        score = num_clusters / num_segments
        results_by_duration[duration]["clusterization_score"] = round(score, 4)
        if 0 < score < best_score:
            best_score = score
            best_duration = duration

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

    return best_result_clean

if __name__ == "__main__":
    from backend.song_metadata import SongMetadata

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
