"""
Audio processing and analysis services for the AI Light Show system.

This package provides audio analysis, pattern detection, and song structure 
analysis capabilities.

Modules:
- arrangement_guess: Song arrangement structure detection
- audio_proccess: Audio preprocessing and noise gating
- demucs_split: Audio stem separation using Demucs
- drums_infer: Drum pattern inference and detection
- essentia_analysis: Audio feature extraction using Essentia
- essentia_chords: Chord detection using Essentia
- pattern_finder: Audio pattern clustering and analysis
- pattern_finder_ml: Machine learning-based pattern detection
"""

# Use lazy imports to avoid issues with problematic dependencies
# Note: Linter may show errors for __all__ items, but they are available via __getattr__
__all__ = [
    # Arrangement analysis
    'guess_arrangement',
    'guess_arrangement_using_drum_patterns',
    
    # Audio processing
    'noise_gate',
    'extract_stems',
    'infer_drums',
    
    # Feature extraction
    'extract_with_essentia',
    'extract_chords_and_align',
    
    # Pattern analysis
    'get_stem_clusters',
    'get_stem_clusters_with_model'
]

def __getattr__(name):
    """Lazy import for audio processing functions."""
    if name == 'guess_arrangement':
        from .arrangement_guess import guess_arrangement
        return guess_arrangement
    elif name == 'guess_arrangement_using_drum_patterns':
        from .arrangement_guess import guess_arrangement_using_drum_patterns
        return guess_arrangement_using_drum_patterns
    elif name == 'noise_gate':
        from .audio_proccess import noise_gate
        return noise_gate
    elif name == 'extract_stems':
        from .demucs_split import extract_stems
        return extract_stems
    elif name == 'infer_drums':
        from .drums_infer import infer_drums
        return infer_drums
    elif name == 'extract_with_essentia':
        from .essentia_analysis import extract_with_essentia
        return extract_with_essentia
    elif name == 'extract_chords_and_align':
        from .essentia_chords import extract_chords_and_align
        return extract_chords_and_align
    elif name == 'get_stem_clusters':
        from .pattern_finder import get_stem_clusters
        return get_stem_clusters
    elif name == 'get_stem_clusters_with_model':
        from .pattern_finder_ml import get_stem_clusters_with_model
        return get_stem_clusters_with_model
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")