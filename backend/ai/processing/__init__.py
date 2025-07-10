"""
Audio processing modules for the AI Light Show backend.

Contains utilities for audio analysis, feature extraction, and
audio manipulation tasks.
"""

from .audio_proccess import noise_gate
from .demucs_split import extract_stems
from .essentia_analysis import extract_with_essentia
from .essentia_chords import extract_chords_and_align

__all__ = [
    'noise_gate',
    'extract_stems',
    'extract_with_essentia', 
    'extract_chords_and_align'
]
