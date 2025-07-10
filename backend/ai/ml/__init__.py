"""
Machine Learning modules for audio analysis and pattern recognition.

Contains ML models for drum detection, pattern finding, and other
audio analysis tasks.
"""

from .drums_infer import infer_drums
from .pattern_finder import get_stem_clusters
from .pattern_finder_ml import get_stem_clusters_with_model, get_model_and_processor

__all__ = [
    'infer_drums',
    'get_stem_clusters', 
    'get_stem_clusters_with_model',
    'get_model_and_processor'
]
