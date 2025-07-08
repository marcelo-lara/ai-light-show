from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .pattern_finder_utils import get_rhythmic_features, get_temporal_features

def perform_clustering(X, max_clusters=8):
    """Perform clustering on feature matrix."""
    best_n_clusters = 2
    if max_clusters >= 3:
        n_segments = len(X)
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

    clustering = AgglomerativeClustering(
        n_clusters=best_n_clusters,
        linkage='ward'
    )
    return clustering.fit_predict(X)

def calculate_similarity_matrix(cluster_centroids):
    """Calculate similarity matrix for cluster centroids."""
    labels_sorted = sorted(cluster_centroids.keys())
    if len(labels_sorted) > 1:
        centroid_array = np.array([cluster_centroids[k] for k in labels_sorted])
        similarity_matrix = cosine_similarity(centroid_array)
        return (similarity_matrix * 100).round(1)
    else:
        return np.array([[100.0]])
