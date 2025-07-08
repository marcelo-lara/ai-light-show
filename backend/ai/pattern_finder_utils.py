import librosa
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from scipy.cluster.hierarchy import linkage
from kneed import KneeLocator
from collections import Counter

def get_rhythmic_features(audio, sr, beats):
    """Extract drum-specific rhythmic features with transient analysis."""
    try:
        onset_frames = librosa.onset.onset_detect(y=audio, sr=sr, units='frames')
        transients = len(onset_frames)
        transient_rate = transients / (len(audio)/sr) if len(audio) > 0 else 0
        onset_env = librosa.onset.onset_strength(y=audio, sr=sr)
        onset_mean = np.mean(onset_env) if len(onset_env) > 0 else 0
        return {
            'transient_count': transients,
            'transient_rate': transient_rate,
            'onset_strength': [onset_mean, 0, 0]
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
