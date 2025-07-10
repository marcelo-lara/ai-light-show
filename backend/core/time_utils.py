"""
Time conversion utilities for the AI Light Show backend.

Provides functions for converting between different time representations
used throughout the system (beats, seconds, milliseconds).
"""

from typing import Union
from ..types import BeatPosition


def beats_to_seconds(beats: float, bpm: float) -> float:
    """
    Convert beats to seconds based on BPM.
    
    Args:
        beats: Number of beats
        bpm: Beats per minute
        
    Returns:
        Time in seconds
        
    Raises:
        ValueError: If bpm is <= 0
    """
    if bpm <= 0:
        raise ValueError("BPM must be greater than 0")
    return (beats / bpm) * 60.0


def seconds_to_beats(seconds: float, bpm: float) -> BeatPosition:
    """
    Convert seconds to beats based on BPM.
    
    Args:
        seconds: Time in seconds
        bpm: Beats per minute
        
    Returns:
        Beat position
        
    Raises:
        ValueError: If bpm is <= 0
    """
    if bpm <= 0:
        raise ValueError("BPM must be greater than 0")
    return (seconds * bpm) / 60.0


def ms_to_seconds(milliseconds: Union[int, float]) -> float:
    """
    Convert milliseconds to seconds.
    
    Args:
        milliseconds: Time in milliseconds
        
    Returns:
        Time in seconds
    """
    return milliseconds / 1000.0


def seconds_to_ms(seconds: float) -> int:
    """
    Convert seconds to milliseconds.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Time in milliseconds (rounded to nearest int)
    """
    return round(seconds * 1000)


def format_time_display(seconds: float) -> str:
    """
    Format time in seconds to MM:SS display format.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string (e.g., "03:45")
    """
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def parse_time_reference(time_ref: str, song_duration: float) -> float:
    """
    Parse various time reference formats to seconds.
    
    Args:
        time_ref: Time reference ("1:30", "90s", "1.5m", etc.)
        song_duration: Total song duration for percentage calculations
        
    Returns:
        Time in seconds
        
    Raises:
        ValueError: If time reference format is invalid
    """
    time_ref = time_ref.strip().lower()
    
    # Handle MM:SS format
    if ":" in time_ref:
        try:
            parts = time_ref.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return minutes * 60 + seconds
        except ValueError:
            pass
    
    # Handle seconds (e.g., "90s", "90")
    if time_ref.endswith("s"):
        try:
            return float(time_ref[:-1])
        except ValueError:
            pass
    
    # Handle minutes (e.g., "1.5m")
    if time_ref.endswith("m"):
        try:
            return float(time_ref[:-1]) * 60
        except ValueError:
            pass
    
    # Handle percentage (e.g., "50%")
    if time_ref.endswith("%"):
        try:
            percentage = float(time_ref[:-1]) / 100
            return song_duration * percentage
        except ValueError:
            pass
    
    # Try parsing as plain number (assume seconds)
    try:
        return float(time_ref)
    except ValueError:
        pass
    
    raise ValueError(f"Invalid time reference format: {time_ref}")
