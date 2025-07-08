from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .pattern_finder_utils import get_rhythmic_features, get_temporal_features

def get_stem_clusters_sliding_window(
    stem_file,
    full_file=None,
    n_mels=64,
    fmax=8000,
    window_duration=4,
    hop_duration=0.5,
    debug=False
):
    """
    Find repeated patterns using sliding window approach.
    """
    # Define missing variables before using them
    consolidated_labels = []
    consolidated_segments = []
    cluster_centroids = {}
    similarity_percent = np.array([[100.0]])

    # ...existing code from get_stem_clusters_sliding_window...

    # Add the missing definition for result
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

    return result
