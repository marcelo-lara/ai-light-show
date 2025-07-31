"""
Extract beats, RMS, and flux from audio files for the /analyze endpoint.
"""

import essentia.standard as es
import essentia
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import logging

essentia.log.infoActive = False
logger = logging.getLogger(__name__)


def analyze_beats_rms_flux(audio_path: str) -> Dict[str, Any]:
    """
    Extracts beats, RMS, and flux from an audio file using Essentia.

    Args:
        audio_path: Path to the audio file (.mp3, .wav, etc.).

    Returns:
        A dictionary with detailed analysis results, including:
        - times: Time in seconds for each analysis frame.
        - beats: Beat markers (1.0 for a beat, 0.0 otherwise) for each frame.
        - rms: RMS value for each frame.
        - flux: Spectral flux for each frame.
        - beat_times: A list of timestamps for detected beats.
        - bpm: Estimated BPM of the song.
    """
    logger.info(f"🎧 Analyzing beats, RMS, and flux for: {audio_path}")
        
    # Load audio (mono)
    loader = es.MonoLoader(filename=audio_path)
    audio = loader()
    
    # Analysis parameters
    frame_size = 1024
    hop_size = 256
    sample_rate = 44100
    
    # Initialize extractors
    window = es.Windowing(type="hann")
    spectrum = es.Spectrum()
    rms_extractor = es.RMS()
    rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
    
    # Extract beats
    bpm, beat_times, confidence, bpm_estimates, bpm_intervals = rhythm_extractor(audio)
    beat_times = [float(b) for b in beat_times]
    logger.info(f"RhythmExtractor2013 confidence: {confidence:.2f}")
    
    # Extract RMS and flux frame by frame
    times = []
    rms_values = []
    flux_values = []
    prev_spec = None
    
    for i, frame in enumerate(es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size, startFromZero=True)):
        t = (i * hop_size) / sample_rate
        
        # RMS calculation
        rms_val = float(rms_extractor(frame))
        
        # Spectral flux calculation
        win = window(frame)
        spec = spectrum(win)
        
        if prev_spec is not None:
            flux_val = float(np.sum(np.clip(spec - prev_spec, 0, None)))
        else:
            flux_val = 0.0
        prev_spec = spec
        
        times.append(round(t, 4))
        rms_values.append(round(rms_val, 6))
        flux_values.append(round(flux_val, 6))
    
    # Create beat markers for each time point
    beat_markers = []
    beat_tolerance = 0.025  # 25ms tolerance for beat matching
    
    for t in times:
        # Check if this time point is close to a beat
        is_beat = any(abs(t - bt) <= beat_tolerance for bt in beat_times)
        beat_markers.append(1.0 if is_beat else 0.0)
    
    logger.info(f"✅ Analysis complete: {len(times)} frames, {len(beat_times)} beats, BPM={bpm:.1f}")
    
    return {
        "times": times,
        "beats": beat_markers,
        "rms": rms_values,
        "flux": flux_values,
        "bpm": float(bpm),
        "beat_times": beat_times,
        "confidence": float(confidence),
        "bpm_estimates": [float(e) for e in bpm_estimates],
        "bpm_intervals": [float(i) for i in bpm_intervals]
    }


def create_dataframe(analysis_data: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a pandas DataFrame from analysis data.
    
    Args:
        analysis_data: Dictionary from analyze_beats_rms_flux
        
    Returns:
        DataFrame with columns: time, beat, rms, flux
    """
    return pd.DataFrame({
        "time": analysis_data["times"],
        "beat": analysis_data["beats"],
        "rms": analysis_data["rms"],
        "flux": analysis_data["flux"]
    })


def filter_dataframe(df: pd.DataFrame, start_time: Optional[float] = None, end_time: Optional[float] = None) -> pd.DataFrame:
    """
    Filter DataFrame by time range.
    
    Args:
        df: Input DataFrame
        start_time: Start time in seconds (inclusive)
        end_time: End time in seconds (inclusive)
        
    Returns:
        Filtered DataFrame
    """
    if start_time is None and end_time is None:
        return df
    
    mask = pd.Series(True, index=df.index)
    
    if start_time is not None:
        mask &= (df["time"] >= start_time)
    
    if end_time is not None:
        mask &= (df["time"] <= end_time)
    
    return df[mask]


def dataframe_to_response(df: pd.DataFrame) -> Dict[str, List]:
    """
    Converts the analysis DataFrame to the final API response format.

    Args:
        df: DataFrame with time, beat, rms, and flux columns.

    Returns:
        A dictionary containing:
        - beats: A list of beat timestamps (in seconds).
        - rms: A list of RMS values for each frame.
        - flux: A list of spectral flux values for each frame.
    """
    # Extract beat times (where beat == 1.0)
    beats = df[df["beat"] == 1.0]["time"].tolist()
    
    # Extract all RMS and flux values
    rms = df["rms"].tolist()
    flux = df["flux"].tolist()
    
    return {
        "beats": beats,
        "rms": rms,
        "flux": flux
    }
