"""
Audio analysis services for song analysis.
"""

from .essentia_analysis import extract_with_essentia
from .demucs_split import extract_stems
from .pattern_finder import get_stem_clusters
from .audio_process import noise_gate
from .arrangement_guess import guess_arrangement, guess_arrangement_using_drum_patterns
from .section_features import (
    extract_section_features,
    extract_song_features,
    extract_features_from_stems
)

__all__ = [
    'extract_with_essentia',
    'extract_stems', 
    'get_stem_clusters',
    'noise_gate',
    'guess_arrangement',
    'guess_arrangement_using_drum_patterns',
    'extract_section_features',
    'extract_song_features',
    'extract_features_from_stems'
]
