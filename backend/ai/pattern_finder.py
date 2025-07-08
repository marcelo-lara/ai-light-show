import warnings
warnings.filterwarnings("ignore")

import os
import numpy as np
import librosa
import soundfile as sf
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import linkage
from kneed import KneeLocator
from pathlib import Path
from collections import Counter
import json

def get_rhythmic_features(audio, sr, beats):
    """Extract drum-specific rhythmic features with transient analysis."""
    try:
        # Simplified rhythmic features to avoid potential infinite loops
        onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='frames')
        transients = len(onset_frames)
        transient_rate = transients / (len(audio)/sr) if len(audio) > 0 else 0
        
        # Simple onset strength
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_mean = np.mean(onset_env) if len(onset_env) > 0 else 0
        
        return {
            'transient_count': transients,
            'transient_rate': transient_rate,
            'onset_strength': [onset_mean, 0, 0]  # Simplified to avoid complex operations
        }
    except Exception as e:
        print(f"⚠️ Rhythmic feature error: {str(e)}")
        return {
            'transient_count': 0,
            'transient_rate': 0,
            'onset_strength': [0, 0, 0]
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
    segment_beat_lengths=(4, 8, 16),  # Longer segments for meaningful pattern detection
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

        # Create non-overlapping segments for better pattern recognition
        segments = []
        i = 0
        while i + duration_beats <= len(beats) - 1:
            start_time = float(beats[int(i)])
            end_time = float(beats[int(i + duration_beats)])
            segments.append((start_time, end_time))
            i += duration_beats  # Non-overlapping segments

        if len(segments) < 2:
            if debug:
                print(f"⚠️ Not enough segments for {duration_beats} beats — skipping...")
            continue

        features, silence_indices = [], []
        
        # Extract features from each segment
        if debug:
            print(f"   Extracting features from {len(segments)} segments...")
        for idx, (start, end) in enumerate(segments):
            if debug and idx % 5 == 0:
                print(f"   Processing segment {idx}/{len(segments)}")
                
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            audio = y[start_sample:end_sample]
            
            # Check for silence with stricter threshold
            if np.mean(np.abs(audio)) < 1e-4:
                silence_indices.append(idx)
                features.append(None)  # Placeholder for silence
                continue
            
            # Extract comprehensive features
            S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels, fmax=fmax)
            log_S = librosa.power_to_db(S, ref=np.max) if S.size > 0 else np.zeros((n_mels, 1))
            
            # Temporal features
            temporal = get_temporal_features(audio, sr, n_mels)
            rhythmic = get_rhythmic_features(audio, sr, beats)
            
            # Spectral features
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr) if len(audio) > 0 else np.zeros((12, 1))
            spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr) if len(audio) > 0 else np.zeros((7, 1))
            rms = librosa.feature.rms(y=audio) if len(audio) > 0 else np.zeros((1, 1))
            
            # Enhanced drum-specific features
            onset_strength = librosa.onset.onset_strength(y=audio, sr=sr)
            onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='frames')
            onset_density = len(onset_frames) / (len(audio)/sr) if len(audio) > 0 else 0
            
            # Spectral rolloff and centroid for timbre characterization
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            
            # Zero crossing rate for percussive content
            zcr = librosa.feature.zero_crossing_rate(audio)
            
            # Combine all features into a comprehensive vector
            feature_vector = np.hstack([
                np.mean(log_S, axis=1),  # Mel spectrogram statistics
                np.std(log_S, axis=1),
                np.mean(temporal['mfcc'], axis=1),  # MFCC features
                np.mean(temporal['delta_mfcc'], axis=1),
                np.mean(temporal['delta2_mfcc'], axis=1),
                np.mean(chroma, axis=1),  # Harmonic content
                np.mean(spectral_contrast, axis=1),  # Spectral shape
                np.mean(spectral_centroid),  # Timbral brightness
                np.mean(spectral_rolloff),   # Spectral rolloff
                np.mean(rms),               # Energy
                np.std(rms),                # Energy variation
                np.mean(onset_strength),    # Onset characteristics
                np.std(onset_strength),
                onset_density,              # Rhythmic density
                np.mean(zcr),              # Percussive content
                rhythmic['transient_count'],  # Transient analysis
                rhythmic['transient_rate']
            ])
            
            features.append(feature_vector)

        # Filter out silence and create feature matrix
        if debug:
            print(f"   Filtering silence from {len(features)} features...")
        non_silence_features = [f for i, f in enumerate(features) if i not in silence_indices and f is not None]
        non_silence_indices = [i for i in range(len(features)) if i not in silence_indices and features[i] is not None]
        
        if len(non_silence_features) < 2:
            if debug:
                print(f"⚠️ Not enough non-silent segments for {duration_beats} beats — skipping...")
            continue

        if debug:
            print(f"   Creating feature matrix from {len(non_silence_features)} non-silent features...")
        X = np.array(non_silence_features)
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
        
        # Standardize features
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        except ValueError:
            X_scaled = X
            
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e6, neginf=-1e6)
        
        # Apply PCA for dimensionality reduction
        if X_scaled.shape[1] > 10:  # Only apply PCA if we have many features
            pca = PCA(n_components=0.95)  # Keep 95% variance
            try:
                X_reduced = pca.fit_transform(X_scaled)
            except ValueError:
                X_reduced = X_scaled
        else:
            X_reduced = X_scaled
            
        X_reduced = np.nan_to_num(X_reduced, nan=0.0)

        # Determine optimal number of clusters using simpler heuristics
        max_clusters = min(len(non_silence_features) - 1, 8)  # Reduced upper bound
        best_n_clusters = 2
        
        if max_clusters >= 3:
            # Use a simple heuristic: aim for 3-8 clusters for music patterns
            # Choose based on number of segments
            n_segments = len(non_silence_features)
            if n_segments <= 5:
                best_n_clusters = 2
            elif n_segments <= 10:
                best_n_clusters = 3
            elif n_segments <= 20:
                best_n_clusters = 4
            elif n_segments <= 40:
                best_n_clusters = 5
            else:
                best_n_clusters = min(6, max_clusters)

        # Perform final clustering
        clustering = AgglomerativeClustering(
            n_clusters=best_n_clusters,
            linkage='ward'
        )
        non_silence_labels = clustering.fit_predict(X_reduced)

        # Map back to all segments (including silence)
        cluster_labels = []
        non_silence_idx = 0
        for i in range(len(segments)):
            if i in silence_indices:
                cluster_labels.append(0)  # Silence cluster
            else:
                cluster_labels.append(non_silence_labels[non_silence_idx] + 1)  # Offset by 1 for silence
                non_silence_idx += 1

        # Calculate cluster centroids and similarity matrix
        cluster_vectors = {}
        for i, label in enumerate(cluster_labels):
            if label == 0:  # Silence
                continue
            feature_idx = non_silence_indices.index(i) if i in non_silence_indices else None
            if feature_idx is not None:
                cluster_vectors.setdefault(label, []).append(X[feature_idx])

        cluster_centroids = {0: np.zeros(X.shape[1] if len(X) > 0 else 1)}  # Silence centroid
        for label, vectors in cluster_vectors.items():
            cluster_centroids[label] = np.mean(vectors, axis=0)

        # Calculate similarity matrix (but don't use it for merging - threshold removed)
        labels_sorted = sorted(cluster_centroids.keys())
        if len(labels_sorted) > 1:
            centroid_array = np.array([cluster_centroids[k] for k in labels_sorted])
            similarity_matrix = cosine_similarity(centroid_array)
            similarity_percent = (similarity_matrix * 100).round(1)
        else:
            similarity_percent = np.array([[100.0]])

        # REMOVED: Cluster similarity merging stage to avoid over-merging
        # Keep all original clusters as detected by the algorithm

        results_by_duration[duration_beats] = {
            "cluster_labels": cluster_labels,
            "segments": segments,
            "n_clusters": len(set(cluster_labels)),
            "cluster_centroids": {str(k): v.tolist() for k, v in cluster_centroids.items()},
            "similarity_matrix": similarity_percent.tolist()
        }

        if debug:
            print(f"   → Clusters: {len(set(cluster_labels))}")
            print(f"   → Segments: {len(segments)}")
            print(f"   → Score: {round(len(set(cluster_labels)) / len(segments), 4)}")
            if len(labels_sorted) > 1:
                print("Similarity Matrix (%):")
                header = "     " + "  ".join(f"C{i}" for i in labels_sorted)
                print(header)
                for i, row in enumerate(similarity_percent):
                    row_str = "  ".join(f"{val:5.1f}" for val in row)
                    print(f"  C{labels_sorted[i]} {row_str}")

    # Select the best result based on segment length and cluster quality
    best_duration = None
    best_score = -1
    
    # First set best_duration_beats for all results
    for duration, result in results_by_duration.items():
        result["best_duration_beats"] = duration
        
        # Calculate a quality score based on:
        # 1. Reasonable number of clusters (3-12 is good for music patterns)
        # 2. Reasonable number of segments (not too many tiny segments)
        # 3. Preference for longer segment durations (more meaningful patterns)
        n_clusters = result["n_clusters"]
        n_segments = len(result["segments"])
        
        if n_segments == 0:
            continue
            
        # Quality factors
        cluster_quality = 1.0 if 3 <= n_clusters <= 12 else 0.5  # Prefer reasonable cluster counts
        segment_quality = min(1.0, 50 / n_segments) if n_segments > 0 else 0  # Prefer fewer, longer segments
        duration_quality = min(1.0, duration / 8)  # Prefer longer segment durations
        
        # Combined score
        score = cluster_quality * segment_quality * duration_quality * n_clusters / n_segments
        result["quality_score"] = score
        
        if score > best_score:
            best_score = score
            best_duration = duration

    # Fallback if no good result found
    if not best_duration and results_by_duration:
        best_duration = max(results_by_duration.keys())  # Choose longest segment duration

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

    # Consolidate consecutive segments with same cluster into longer patterns
    if best_result and "segments" in best_result and "cluster_labels" in best_result:
        consolidated_segments = []
        consolidated_labels = []
        
        if len(best_result["segments"]) > 0:
            current_start = best_result["segments"][0][0]
            current_end = best_result["segments"][0][1]
            current_label = best_result["cluster_labels"][0]
            
            for i in range(1, len(best_result["segments"])):
                seg_start, seg_end = best_result["segments"][i]
                seg_label = best_result["cluster_labels"][i]
                
                # If same cluster, extend current segment
                if seg_label == current_label:
                    current_end = seg_end
                else:
                    # Save current segment and start new one
                    consolidated_segments.append((current_start, current_end))
                    consolidated_labels.append(current_label)
                    current_start = seg_start
                    current_end = seg_end
                    current_label = seg_label
            
            # Add the last segment
            consolidated_segments.append((current_start, current_end))
            consolidated_labels.append(current_label)
            
            # Update best_result with consolidated data
            best_result["segments"] = consolidated_segments
            best_result["cluster_labels"] = consolidated_labels
            best_result["n_clusters"] = len(set(consolidated_labels))

    # Post-process to consolidate and clean segments
    if best_result and "segments" in best_result and "cluster_labels" in best_result:
        # First trim overlapping segments
        cleaned_segments = []
        last_end = -1.0
        for (start, end), label in zip(best_result["segments"], best_result["cluster_labels"]):
            if start < last_end:
                # Adjust previous segment end to current start
                if cleaned_segments:
                    prev_seg, prev_label = cleaned_segments[-1]
                    cleaned_segments[-1] = ((prev_seg[0], start), prev_label)
            cleaned_segments.append(((start, end), label))
            last_end = end

        # Create clusters_timeline for final output
        best_result["clusters_timeline"] = [
            {
                "start": float(start),
                "end": float(end),
                "cluster": int(cluster)
            }
            for (start, end), cluster in cleaned_segments
        ]
        
        # Update segments and labels with cleaned data
        best_result["segments"] = [s for s, _ in cleaned_segments]
        best_result["cluster_labels"] = [c for _, c in cleaned_segments]

    # Convert to JSON-serializable format
    def make_json_serializable(obj):
        """Convert numpy types and other non-serializable objects to JSON-compatible types."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {str(k): make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(make_json_serializable(item) for item in obj)
        else:
            return obj
            
    best_result_clean = make_json_serializable(best_result)

    if best_result_clean.get("n_clusters", 0) == 0:
        print("⚠️ No clusters found after processing.")
        return None

    if best_result_clean.get("n_clusters", 0) > 50:
        print("⚠️ Too many clusters found, likely too noisy or complex.")
        return None

    return best_result_clean

def get_stem_clusters_time_based(
    stem_file,
    full_file=None,
    n_mels=64,
    fmax=8000,
    segment_durations=(4, 8, 12),  # Smaller time-based segments in seconds
    debug=False
):
    """
    Find repeated patterns in a stem file using time-based segmentation.
    This approach uses fixed time intervals instead of beat-based segmentation.
    """
    print(f"⛓️ Analyzing stem clusters (time-based)")

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
            "best_duration_seconds": 0,
            "all_durations": {}
        }

    audio_duration = len(y) / sr
    results_by_duration = {}

    for duration_sec in segment_durations:
        if debug:
            print(f"\n⎱Segment duration: {duration_sec} seconds")

        # Create non-overlapping time-based segments
        segments = []
        current_time = 0
        while current_time + duration_sec <= audio_duration:
            start_time = current_time
            end_time = current_time + duration_sec
            segments.append((start_time, end_time))
            current_time += duration_sec

        # Add final segment if there's remaining audio
        if current_time < audio_duration:
            segments.append((current_time, audio_duration))

        if len(segments) < 2:
            if debug:
                print(f"⚠️ Not enough segments for {duration_sec} seconds — skipping...")
            continue

        features, silence_indices = [], []
        
        # Extract features from each segment
        if debug:
            print(f"   Extracting features from {len(segments)} segments...")
        
        for idx, (start, end) in enumerate(segments):
            if debug and idx % 5 == 0:
                print(f"   Processing segment {idx}/{len(segments)}")
                
            start_sample = int(start * sr)
            end_sample = int(end * sr)
            audio = y[start_sample:end_sample]
            
            # Check for silence with stricter threshold
            if np.mean(np.abs(audio)) < 1e-4:
                silence_indices.append(idx)
                features.append(None)
                continue
            
            # Extract comprehensive features (same as beat-based version)
            S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels, fmax=fmax)
            log_S = librosa.power_to_db(S, ref=np.max) if S.size > 0 else np.zeros((n_mels, 1))
            
            # Temporal features
            temporal = get_temporal_features(audio, sr, n_mels)
            rhythmic = get_rhythmic_features(audio, sr, [start + i for i in range(int(end-start))])
            
            # Spectral features
            chroma = librosa.feature.chroma_stft(y=audio, sr=sr) if len(audio) > 0 else np.zeros((12, 1))
            spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr) if len(audio) > 0 else np.zeros((7, 1))
            rms = librosa.feature.rms(y=audio) if len(audio) > 0 else np.zeros((1, 1))
            
            # Enhanced drum-specific features
            onset_strength = librosa.onset.onset_strength(y=audio, sr=sr)
            onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='frames')
            onset_density = len(onset_frames) / (len(audio)/sr) if len(audio) > 0 else 0
            
            # Spectral rolloff and centroid for timbre characterization
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            
            # Zero crossing rate for percussive content
            zcr = librosa.feature.zero_crossing_rate(audio)
            
            # Combine all features into a comprehensive vector
            feature_vector = np.hstack([
                np.mean(log_S, axis=1),
                np.std(log_S, axis=1),
                np.mean(temporal['mfcc'], axis=1),
                np.mean(temporal['delta_mfcc'], axis=1),
                np.mean(temporal['delta2_mfcc'], axis=1),
                np.mean(chroma, axis=1),
                np.mean(spectral_contrast, axis=1),
                np.mean(spectral_centroid),
                np.mean(spectral_rolloff),
                np.mean(rms),
                np.std(rms),
                np.mean(onset_strength),
                np.std(onset_strength),
                onset_density,
                np.mean(zcr),
                rhythmic['transient_count'],
                rhythmic['transient_rate']
            ])
            
            features.append(feature_vector)

        # Filter out silence and create feature matrix
        if debug:
            print(f"   Filtering silence from {len(features)} features...")
        non_silence_features = [f for i, f in enumerate(features) if i not in silence_indices and f is not None]
        non_silence_indices = [i for i in range(len(features)) if i not in silence_indices and features[i] is not None]
        
        if len(non_silence_features) < 2:
            if debug:
                print(f"⚠️ Not enough non-silent segments for {duration_sec} seconds — skipping...")
            continue

        X = np.array(non_silence_features)
        X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
        
        # Standardize features
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        except ValueError:
            X_scaled = X
            
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e6, neginf=-1e6)
        
        # Apply PCA for dimensionality reduction
        if X_scaled.shape[1] > 10:
            pca = PCA(n_components=0.95)
            try:
                X_reduced = pca.fit_transform(X_scaled)
            except ValueError:
                X_reduced = X_scaled
        else:
            X_reduced = X_scaled
            
        X_reduced = np.nan_to_num(X_reduced, nan=0.0)

        # Determine optimal number of clusters
        max_clusters = min(len(non_silence_features) - 1, 8)
        best_n_clusters = 2
        
        if max_clusters >= 3:
            n_segments = len(non_silence_features)
            if n_segments <= 5:
                best_n_clusters = 2
            elif n_segments <= 10:
                best_n_clusters = 3
            elif n_segments <= 20:
                best_n_clusters = 4
            elif n_segments <= 40:
                best_n_clusters = 5
            else:
                best_n_clusters = min(6, max_clusters)

        # Perform clustering
        clustering = AgglomerativeClustering(
            n_clusters=best_n_clusters,
            linkage='ward'
        )
        non_silence_labels = clustering.fit_predict(X_reduced)

        # Map back to all segments (including silence)
        cluster_labels = []
        non_silence_idx = 0
        for i in range(len(segments)):
            if i in silence_indices:
                cluster_labels.append(0)  # Silence cluster
            else:
                cluster_labels.append(non_silence_labels[non_silence_idx] + 1)
                non_silence_idx += 1

        # Calculate cluster centroids and similarity matrix
        cluster_vectors = {}
        for i, label in enumerate(cluster_labels):
            if label == 0:  # Silence
                continue
            feature_idx = non_silence_indices.index(i) if i in non_silence_indices else None
            if feature_idx is not None:
                cluster_vectors.setdefault(label, []).append(X[feature_idx])

        cluster_centroids = {0: np.zeros(X.shape[1] if len(X) > 0 else 1)}
        for label, vectors in cluster_vectors.items():
            cluster_centroids[label] = np.mean(vectors, axis=0)

        # Calculate similarity matrix
        labels_sorted = sorted(cluster_centroids.keys())
        if len(labels_sorted) > 1:
            centroid_array = np.array([cluster_centroids[k] for k in labels_sorted])
            similarity_matrix = cosine_similarity(centroid_array)
            similarity_percent = (similarity_matrix * 100).round(1)
        else:
            similarity_percent = np.array([[100.0]])

        results_by_duration[duration_sec] = {
            "cluster_labels": cluster_labels,
            "segments": segments,
            "n_clusters": len(set(cluster_labels)),
            "cluster_centroids": {str(k): v.tolist() for k, v in cluster_centroids.items()},
            "similarity_matrix": similarity_percent.tolist()
        }

        if debug:
            print(f"   → Clusters: {len(set(cluster_labels))}")
            print(f"   → Segments: {len(segments)}")
            print(f"   → Score: {round(len(set(cluster_labels)) / len(segments), 4)}")

    # Select the best result (same logic as beat-based version)
    best_duration = None
    best_score = -1
    
    for duration, result in results_by_duration.items():
        result["best_duration_seconds"] = duration
        
        n_clusters = result["n_clusters"]
        n_segments = len(result["segments"])
        
        if n_segments == 0:
            continue
            
        cluster_quality = 1.0 if 3 <= n_clusters <= 12 else 0.5
        segment_quality = min(1.0, 50 / n_segments) if n_segments > 0 else 0
        duration_quality = min(1.0, duration / 16)
        
        score = cluster_quality * segment_quality * duration_quality * n_clusters / n_segments
        result["quality_score"] = score
        
        if score > best_score:
            best_score = score
            best_duration = duration

    if not best_duration and results_by_duration:
        best_duration = max(results_by_duration.keys())

    best_result = results_by_duration.get(best_duration, {})
    best_result["best_duration_seconds"] = best_duration
    best_result["all_durations"] = {
        str(k): {
            "n_clusters": v["n_clusters"],
            "n_segments": len(v["segments"]),
            "clusterization_score": round(v["n_clusters"] / len(v["segments"]), 4) if len(v["segments"]) else None
        }
        for k, v in results_by_duration.items()
    }
    
    if str(best_duration) in best_result["all_durations"]:
        best_result["clusterization_score"] = best_result["all_durations"][str(best_duration)]["clusterization_score"]
    else:
        best_result["clusterization_score"] = 0.0

    # Consolidate consecutive segments with same cluster and add beat alignment
    if best_result and "segments" in best_result and "cluster_labels" in best_result:
        # Load beats if full file is available for beat alignment
        beats = None
        if full_file and os.path.exists(full_file):
            try:
                y_full, sr_full = librosa.load(full_file, sr=None)
                tempo, beat_frames = librosa.beat.beat_track(y=y_full, sr=sr_full)
                beats = librosa.frames_to_time(beat_frames, sr=sr_full)
                if debug:
                    print(f"   Loaded {len(beats)} beats for alignment (tempo: {round(float(tempo), 1)} BPM)")
            except Exception as e:
                if debug:
                    print(f"   ⚠️ Could not extract beats for alignment: {e}")
        
        consolidated_segments = []
        consolidated_labels = []
        
        if len(best_result["segments"]) > 0:
            current_start = best_result["segments"][0][0]
            current_end = best_result["segments"][0][1]
            current_label = best_result["cluster_labels"][0]
            
            for i in range(1, len(best_result["segments"])):
                seg_start, seg_end = best_result["segments"][i]
                seg_label = best_result["cluster_labels"][i]
                
                if seg_label == current_label:
                    current_end = seg_end
                else:
                    # Pattern change detected - apply beat alignment
                    if beats is not None and len(beats) > 0:
                        # Find the nearest beat to the segment boundary
                        beat_distances = np.abs(beats - seg_start)
                        nearest_beat_idx = np.argmin(beat_distances)
                        nearest_beat_time = beats[nearest_beat_idx]
                        
                        # Only align if the nearest beat is within reasonable distance (±2 seconds)
                        if beat_distances[nearest_beat_idx] <= 2.0:
                            aligned_boundary = nearest_beat_time
                            if debug and abs(seg_start - aligned_boundary) > 0.5:
                                print(f"   🎵 Beat alignment: {seg_start:.2f}s → {aligned_boundary:.2f}s (beat {nearest_beat_idx})")
                        else:
                            aligned_boundary = seg_start
                    else:
                        aligned_boundary = seg_start
                    
                    # Add segment with aligned boundary
                    consolidated_segments.append((current_start, aligned_boundary))
                    consolidated_labels.append(current_label)
                    current_start = aligned_boundary
                    current_end = seg_end
                    current_label = seg_label
            
            consolidated_segments.append((current_start, current_end))
            consolidated_labels.append(current_label)
            
            best_result["segments"] = consolidated_segments
            best_result["cluster_labels"] = consolidated_labels
            best_result["n_clusters"] = len(set(consolidated_labels))

    # Create final clusters_timeline
    if best_result and "segments" in best_result and "cluster_labels" in best_result:
        best_result["clusters_timeline"] = [
            {
                "start": float(start),
                "end": float(end),
                "cluster": int(cluster)
            }
            for (start, end), cluster in zip(best_result["segments"], best_result["cluster_labels"])
        ]

    # Convert to JSON-serializable format
    def make_json_serializable(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {str(k): make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(make_json_serializable(item) for item in obj)
        else:
            return obj
            
    best_result_clean = make_json_serializable(best_result)

    if best_result_clean.get("n_clusters", 0) == 0:
        print("⚠️ No clusters found after processing.")
        return None

    if best_result_clean.get("n_clusters", 0) > 50:
        print("⚠️ Too many clusters found, likely too noisy or complex.")
        return None

    return best_result_clean

def get_stem_clusters_sliding_window(
    stem_file,
    full_file=None,
    n_mels=64,
    fmax=8000,
    window_duration=4,  # Smaller window size in seconds (was 8)
    hop_duration=0.5,   # Much smaller step size in seconds (was 2)
    debug=False
):
    """
    Find repeated patterns using sliding window approach.
    Uses overlapping windows to better capture pattern transitions.
    """
    print(f"⛓️ Analyzing stem clusters (sliding window)")

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
            "best_duration_seconds": window_duration,
            "all_durations": {}
        }

    audio_duration = len(y) / sr
    
    if debug:
        print(f"\n⎱Window: {window_duration}s, Hop: {hop_duration}s")

    # Create sliding windows
    segments = []
    current_time = 0
    while current_time + window_duration <= audio_duration:
        start_time = current_time
        end_time = current_time + window_duration
        segments.append((start_time, end_time))
        current_time += hop_duration

    # Add final window if there's remaining audio
    if current_time < audio_duration and audio_duration - current_time >= window_duration / 2:
        segments.append((current_time, audio_duration))

    if len(segments) < 2:
        if debug:
            print(f"⚠️ Not enough segments for sliding window — skipping...")
        return None

    features, silence_indices = [], []
    
    # Extract features from each segment
    if debug:
        print(f"   Extracting features from {len(segments)} overlapping segments...")
    
    for idx, (start, end) in enumerate(segments):
        if debug and idx % 10 == 0:
            print(f"   Processing segment {idx}/{len(segments)}")
            
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        audio = y[start_sample:end_sample]
        
        # Check for silence with stricter threshold
        if np.mean(np.abs(audio)) < 1e-4:
            silence_indices.append(idx)
            features.append(None)
            continue
        
        # Extract comprehensive features
        S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=n_mels, fmax=fmax)
        log_S = librosa.power_to_db(S, ref=np.max) if S.size > 0 else np.zeros((n_mels, 1))
        
        # Temporal features
        temporal = get_temporal_features(audio, sr, n_mels)
        rhythmic = get_rhythmic_features(audio, sr, [start + i for i in range(int(end-start))])
        
        # Spectral features
        chroma = librosa.feature.chroma_stft(y=audio, sr=sr) if len(audio) > 0 else np.zeros((12, 1))
        spectral_contrast = librosa.feature.spectral_contrast(y=audio, sr=sr) if len(audio) > 0 else np.zeros((7, 1))
        rms = librosa.feature.rms(y=audio) if len(audio) > 0 else np.zeros((1, 1))
        
        # Enhanced drum-specific features
        onset_strength = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='frames')
        onset_density = len(onset_frames) / (len(audio)/sr) if len(audio) > 0 else 0
        
        # Spectral rolloff and centroid
        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(audio)
        
        # Combine all features
        feature_vector = np.hstack([
            np.mean(log_S, axis=1),
            np.std(log_S, axis=1),
            np.mean(temporal['mfcc'], axis=1),
            np.mean(temporal['delta_mfcc'], axis=1),
            np.mean(temporal['delta2_mfcc'], axis=1),
            np.mean(chroma, axis=1),
            np.mean(spectral_contrast, axis=1),
            np.mean(spectral_centroid),
            np.mean(spectral_rolloff),
            np.mean(rms),
            np.std(rms),
            np.mean(onset_strength),
            np.std(onset_strength),
            onset_density,
            np.mean(zcr),
            rhythmic['transient_count'],
            rhythmic['transient_rate']
        ])
        
        features.append(feature_vector)

    # Filter out silence and create feature matrix
    if debug:
        print(f"   Filtering silence from {len(features)} features...")
    non_silence_features = [f for i, f in enumerate(features) if i not in silence_indices and f is not None]
    non_silence_indices = [i for i in range(len(features)) if i not in silence_indices and features[i] is not None]
    
    if len(non_silence_features) < 2:
        if debug:
            print(f"⚠️ Not enough non-silent segments — skipping...")
        return None

    X = np.array(non_silence_features)
    X = np.nan_to_num(X, nan=0.0, posinf=1e6, neginf=-1e6)
    
    # Standardize features
    try:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
    except ValueError:
        X_scaled = X
        
    X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e6, neginf=-1e6)
    
    # Apply PCA for dimensionality reduction
    if X_scaled.shape[1] > 10:
        pca = PCA(n_components=0.95)
        try:
            X_reduced = pca.fit_transform(X_scaled)
        except ValueError:
            X_reduced = X_scaled
    else:
        X_reduced = X_scaled
        
    X_reduced = np.nan_to_num(X_reduced, nan=0.0)

    # Determine optimal number of clusters
    max_clusters = min(len(non_silence_features) - 1, 10)  # Allow more clusters for sliding window
    best_n_clusters = 3  # Start with 3 for better pattern detection
    
    if max_clusters >= 4:
        n_segments = len(non_silence_features)
        if n_segments <= 10:
            best_n_clusters = 3
        elif n_segments <= 20:
            best_n_clusters = 4
        elif n_segments <= 40:
            best_n_clusters = 6
        elif n_segments <= 80:
            best_n_clusters = 8
        else:
            best_n_clusters = min(10, max_clusters)

    # Perform clustering
    clustering = AgglomerativeClustering(
        n_clusters=best_n_clusters,
        linkage='ward'
    )
    non_silence_labels = clustering.fit_predict(X_reduced)

    # Map back to all segments (including silence)
    cluster_labels = []
    non_silence_idx = 0
    for i in range(len(segments)):
        if i in silence_indices:
            cluster_labels.append(0)  # Silence cluster
        else:
            cluster_labels.append(non_silence_labels[non_silence_idx] + 1)
            non_silence_idx += 1

    # Convert overlapping segments to non-overlapping regions
    if debug:
        print(f"   Converting {len(segments)} overlapping windows to regions...")
    
    # Load beats if full file is available for beat alignment
    beats = None
    if full_file and os.path.exists(full_file):
        try:
            y_full, sr_full = librosa.load(full_file, sr=None)
            tempo, beat_frames = librosa.beat.beat_track(y=y_full, sr=sr_full)
            beats = librosa.frames_to_time(beat_frames, sr=sr_full)
            if debug:
                tempo_val = float(tempo) if hasattr(tempo, '__float__') else tempo
                print(f"   Loaded {len(beats)} beats for alignment (tempo: {tempo_val:.1f} BPM)")
        except Exception as e:
            if debug:
                print(f"   ⚠️ Could not extract beats for alignment: {e}")
    
    # Find cluster transitions using majority voting in overlapping regions
    time_resolution = 0.25  # Finer resolution for transition detection (seconds) - was 0.5
    max_time = max(end for start, end in segments)
    time_points = np.arange(0, max_time, time_resolution)
    cluster_votes = []
    
    for t in time_points:
        votes = []
        for i, (start, end) in enumerate(segments):
            if start <= t < end:
                votes.append(cluster_labels[i])
        
        if votes:
            # Use most common cluster at this time point
            most_common = Counter(votes).most_common(1)[0][0]
            cluster_votes.append(most_common)
        else:
            cluster_votes.append(0)  # Default to silence
    
    # Find cluster boundaries with beat alignment
    consolidated_segments = []
    consolidated_labels = []
    
    if cluster_votes:
        current_cluster = cluster_votes[0]
        current_start = 0
        
        for i, cluster in enumerate(cluster_votes[1:], 1):
            if cluster != current_cluster:
                # Cluster change detected at time_points[i]
                raw_change_time = time_points[i]
                
                # BEAT ALIGNMENT: Align pattern change to nearest beat
                if beats is not None and len(beats) > 0:
                    # Find the nearest beat to the detected change
                    beat_distances = np.abs(beats - raw_change_time)
                    nearest_beat_idx = np.argmin(beat_distances)
                    nearest_beat_time = beats[nearest_beat_idx]
                    
                    # Only align if the nearest beat is within a reasonable distance (±2 seconds)
                    if beat_distances[nearest_beat_idx] <= 2.0:
                        aligned_change_time = nearest_beat_time
                        if debug and abs(raw_change_time - aligned_change_time) > 0.5:
                            print(f"   🎵 Beat alignment: {raw_change_time:.2f}s → {aligned_change_time:.2f}s (beat {nearest_beat_idx})")
                    else:
                        aligned_change_time = raw_change_time
                else:
                    aligned_change_time = raw_change_time
                
                # Add segment with aligned time
                consolidated_segments.append((current_start, aligned_change_time))
                consolidated_labels.append(current_cluster)
                current_start = aligned_change_time
                current_cluster = cluster
        
        # Add final segment
        consolidated_segments.append((current_start, max_time))
        consolidated_labels.append(current_cluster)

    # Calculate cluster centroids for similarity matrix
    cluster_vectors = {}
    for i, label in enumerate(cluster_labels):
        if label == 0:  # Silence
            continue
        feature_idx = non_silence_indices.index(i) if i in non_silence_indices else None
        if feature_idx is not None:
            cluster_vectors.setdefault(label, []).append(X[feature_idx])

    cluster_centroids = {0: np.zeros(X.shape[1] if len(X) > 0 else 1)}
    for label, vectors in cluster_vectors.items():
        cluster_centroids[label] = np.mean(vectors, axis=0)

    # Calculate similarity matrix
    labels_sorted = sorted(cluster_centroids.keys())
    if len(labels_sorted) > 1:
        centroid_array = np.array([cluster_centroids[k] for k in labels_sorted])
        similarity_matrix = cosine_similarity(centroid_array)
        similarity_percent = (similarity_matrix * 100).round(1)
    else:
        similarity_percent = np.array([[100.0]])

    if debug:
        print(f"   → Clusters: {len(set(consolidated_labels))}")
        print(f"   → Segments: {len(consolidated_segments)}")
        print(f"   → Score: {round(len(set(consolidated_labels)) / len(consolidated_segments), 4)}")

    # Create final result
    result = {
        "cluster_labels": consolidated_labels,
        "segments": consolidated_segments,
        "n_clusters": len(set(consolidated_labels)),
        "cluster_centroids": {str(k): v.tolist() for k, v in cluster_centroids.items()},
        "similarity_matrix": similarity_percent.tolist(),
        "best_duration_seconds": window_duration,
        "clusterization_score": round(len(set(consolidated_labels)) / len(consolidated_segments), 4) if consolidated_segments else 0,
        "clusters_timeline": [
            {
                "start": float(start),
                "end": float(end),
                "cluster": int(cluster)
            }
            for (start, end), cluster in zip(consolidated_segments, consolidated_labels)
        ]
    }

    # Convert to JSON-serializable format
    def make_json_serializable(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {str(k): make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_json_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(make_json_serializable(item) for item in obj)
        else:
            return obj
            
    return make_json_serializable(result)

if __name__ == "__main__":
    '''
    Example drums patterns for the song "Born Slippy" by Underworld:
    time range     | pattern | explanation
    0s     - 34.2s  [0]  drum is silent (intro)
    34.2s  - 55.2s  [1]  first kick 
    55.2s  - 81.2s  [2]  a tom is added 
    81.2s  - 97.1s  [3]  tom change pattern
    97.1s  - 117.1s [4]  a tom+hihat pattern
    102.3s - 120s   [5]  a two kicks then two snares pattern* (*could be two clusters, one for the kicks and one for the snares)
    120.3s - 122s   [6]  snare only pattern
    122s   - 130s   [4]  a tom+hihat pattern
    ''' 
    from ..models.song_metadata import SongMetadata

    song = SongMetadata("born_slippy", songs_folder="/home/darkangel/ai-light-show/songs")
    beats = song.get_beats_array()
    stem_file = f"/home/darkangel/ai-light-show/songs/temp/htdemucs/{song.song_name}/drums.wav"

    print("="*60)
    print("Testing BEAT-BASED clustering:")
    print("="*60)
    print(f"Clustering {stem_file} with beat-based segments...")
    beat_result = get_stem_clusters(beats, stem_file, full_file=song.mp3_path, debug=True)

    print(f"\n🏆 Beat-based result:")
    print(f"   → Best duration: {beat_result.get('best_duration_beats')} beats")
    print(f"   → Clusters: {beat_result['n_clusters']}")
    print(f"   → Segments: {len(beat_result['segments'])}")
    print(f"   → Score: {beat_result['clusterization_score']}")

    print("\n" + "="*60)
    print("Testing TIME-BASED clustering:")
    print("="*60)
    print(f"Clustering {stem_file} with time-based segments...")
    time_result = get_stem_clusters_time_based(stem_file, full_file=song.mp3_path, debug=True)

    print(f"\n🏆 Time-based result:")
    print(f"   → Best duration: {time_result.get('best_duration_seconds')} seconds")
    print(f"   → Clusters: {time_result['n_clusters']}")
    print(f"   → Segments: {len(time_result['segments'])}")
    print(f"   → Score: {time_result['clusterization_score']}")

    print("\n" + "="*60)
    print("Testing SLIDING WINDOW clustering (multiple configurations):")
    print("="*60)
    
    # Test different sliding window configurations
    sliding_configs = [
        {"window": 2, "hop": 0.25, "name": "Fine (2s/0.25s)"},
        {"window": 4, "hop": 0.5, "name": "Medium (4s/0.5s)"},
        {"window": 6, "hop": 1.0, "name": "Coarse (6s/1s)"},
        {"window": 8, "hop": 2.0, "name": "Original (8s/2s)"}
    ]
    
    sliding_results = []
    for config in sliding_configs:
        print(f"\nTesting {config['name']} configuration...")
        print(f"Clustering {stem_file} with {config['window']}s window, {config['hop']}s hop...")
        result = get_stem_clusters_sliding_window(
            stem_file, 
            full_file=song.mp3_path, 
            window_duration=config['window'],
            hop_duration=config['hop'],
            debug=True
        )
        sliding_results.append((config['name'], result))
        if result:
            print(f"🏆 {config['name']} result:")
            print(f"   → Window/Hop: {config['window']}s/{config['hop']}s")
            print(f"   → Clusters: {result['n_clusters']}")
            print(f"   → Segments: {len(result['segments'])}")
            print(f"   → Score: {result['clusterization_score']}")

    print("\n" + "="*60)
    print("Testing SLIDING WINDOW clustering:")
    print("="*60)
    print(f"Clustering {stem_file} with sliding window segments...")
    sliding_result = get_stem_clusters_sliding_window(stem_file, full_file=song.mp3_path, debug=True)

    print(f"\n🏆 Sliding window result:")
    print(f"   → Best duration: {sliding_result.get('best_duration_seconds')} seconds")
    print(f"   → Clusters: {sliding_result['n_clusters']}")
    print(f"   → Segments: {len(sliding_result['segments'])}")
    print(f"   → Score: {sliding_result['clusterization_score']}")

    # Compare and choose the best approach
    print("\n" + "="*60)
    print("COMPARISON:")
    print("="*60)
    
    print("\nBeat-based timeline:")
    for item in beat_result.get('clusters_timeline', []):
        start, end, cluster = item['start'], item['end'], item['cluster']
        print(f"  {start:6.1f}-{end:6.1f} [{cluster}] ({end-start:5.1f}s)")
    
    print("\nTime-based timeline:")
    for item in time_result.get('clusters_timeline', []):
        start, end, cluster = item['start'], item['end'], item['cluster']
        print(f"  {start:6.1f}-{end:6.1f} [{cluster}] ({end-start:5.1f}s)")
    
    print("\nSliding window timeline (default config):")
    for item in sliding_result.get('clusters_timeline', []):
        start, end, cluster = item['start'], item['end'], item['cluster']
        print(f"  {start:6.1f}-{end:6.1f} [{cluster}] ({end-start:5.1f}s)")
    
    # Show all sliding window configurations
    for config_name, result in sliding_results:
        if result and result != sliding_result:  # Don't repeat the default one
            print(f"\n{config_name} timeline:")
            for item in result.get('clusters_timeline', []):
                start, end, cluster = item['start'], item['end'], item['cluster']
                print(f"  {start:6.1f}-{end:6.1f} [{cluster}] ({end-start:5.1f}s)")
    
    print("\nTarget human-perceived patterns:")
    print("   time range      | pattern | explanation")
    print("   0s     - 34.2s  | 0       | drum is silent (intro)")
    print("   34.2s  - 55.2s  | 1       | 1 kick + 2 snare pattern")
    print("   55.2s  - 81.2s  | 2       | a tom is added ")
    print("   81.2s  - 97.1s  | 3       | tom change pattern")
    print("   97.1s  - 117.1s | 4       | a tom+hihat pattern")
    print("   102.3s - 120s   | 5       | a two kicks then two snares pattern* (*could be two clusters, one for the kicks and one for the snares)")
    print("   120.3s - 122s   | 6       | snare only pattern")
    print("   122s   - 130s   | 4       | a tom+hihat pattern")

    # Choose the better result - prioritize medium sliding window for best balance
    best_candidates = [
        ("sliding window (Medium 4s/0.5s)", sliding_results[1][1] if len(sliding_results) > 1 else sliding_result),
        ("sliding window (default)", sliding_result),
        ("time-based", time_result),
        ("beat-based", beat_result)
    ]
    
    # Add all sliding window configurations to candidates
    for config_name, result in sliding_results:
        if result and result != sliding_result:  # Don't duplicate default
            best_candidates.append((f"sliding window ({config_name})", result))
    
    # Pick the first valid result with reasonable cluster count
    best_result = None
    approach = None
    
    for name, result in best_candidates:
        if result is not None and result.get('n_clusters', 0) >= 3:
            best_result = result
            approach = name
            break
    
    # Fallback to any valid result
    if best_result is None:
        for name, result in best_candidates:
            if result is not None:
                best_result = result
                approach = name
                break

    print(f"\n🎯 Using {approach} approach for final result")

    if best_result is not None:
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
    else:
        print("⚠️ No valid clustering results generated")


    # time range     | cluster | explanation
    # 0m0.0s  - 0m34.2s  [0]  drum is silent (intro)
    # 0m34.2s - 0m55.2s  [1]  first kick 
    # 0m55.2s - 1m21.2s  [2]  a tom is added 
    # 1m21.2s - 1m37.1s  [3]  tom change pattern
    # 1m37.1s - 117.1    [4]  a tom+hihat pattern
    # 1m42.3s - 2m00s    [5]  a two kicks then two snares pattern* (*could be two clusters, one for the kicks and one for the snares)
    # 2m00.3s - 2m2.0s   [6]  snare only pattern
    # 2m02.0  - 2m10s    [4]  a tom+hihat pattern
