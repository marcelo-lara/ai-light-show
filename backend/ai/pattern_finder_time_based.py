from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def get_stem_clusters_time_based(
    stem_file,
    full_file=None,
    n_mels=64,
    fmax=8000,
    segment_durations=(4, 8, 12),
    debug=False
):
    """
    Find repeated patterns in a stem file using time-based segmentation.
    """
    # Define best_result before using make_json_serializable
    best_result = {}

    # ...existing code from get_stem_clusters_time_based...
    best_result_clean = make_json_serializable(best_result)
    return best_result_clean

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
