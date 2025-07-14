"""
Audio processing utilities including noise gating.
"""

import numpy as np
import soundfile as sf
import librosa
import logging

logger = logging.getLogger(__name__)


def noise_gate(input_path, output_path=None, threshold_db: float = -40.0, frame_length: int = 2048, hop_length: int = 512):
    """
    Applies a noise gate by silencing parts of the audio below a specified RMS threshold.

    Args:
        input_path (str): Path to the input .wav file.
        output_path (str): Path where the processed .wav file will be saved.
        threshold_db (float): RMS threshold in decibels. Anything below is silenced.
        frame_length (int): Window size for RMS calculation.
        hop_length (int): Hop size between frames.
        
    Returns:
        str: Path to the processed audio file.
    """
    if output_path is None:
        output_path = input_path  # Overwrite input file by default

    logger.info(f"  Noise gate | min {threshold_db} dB to {input_path}...")

    # Load audio
    y, sr = librosa.load(input_path, sr=None)

    # Calculate RMS energy per frame
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)

    # Prepare output array
    y_out = np.copy(y)

    # Zero-out samples in frames where RMS < threshold
    for i, db in enumerate(rms_db):
        if db < threshold_db:
            start = i * hop_length
            end = min(start + frame_length, len(y_out))
            y_out[start:end] = 0.0

    # Save processed audio
    sf.write(output_path, y_out, sr)
    return output_path
