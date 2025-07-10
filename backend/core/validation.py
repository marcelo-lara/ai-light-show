"""
Validation utilities for the AI Light Show backend.

Provides validation functions for DMX values, time ranges, and other
system parameters to ensure data integrity.
"""

from typing import Union, List, Optional
from ..types import ChannelValue, TimeReference


def validate_dmx_channel(channel: int) -> bool:
    """
    Validate DMX channel number.
    
    Args:
        channel: DMX channel number (1-512)
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If channel is out of range
    """
    if not isinstance(channel, int):
        raise ValueError(f"DMX channel must be an integer, got {type(channel)}")
    
    if not (1 <= channel <= 512):
        raise ValueError(f"DMX channel must be between 1-512, got {channel}")
    
    return True


def validate_dmx_value(value: ChannelValue) -> bool:
    """
    Validate DMX channel value.
    
    Args:
        value: DMX value (0-255)
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If value is out of range
    """
    if not isinstance(value, int):
        raise ValueError(f"DMX value must be an integer, got {type(value)}")
    
    if not (0 <= value <= 255):
        raise ValueError(f"DMX value must be between 0-255, got {value}")
    
    return True


def validate_time_range(start_time: float, end_time: Optional[float] = None, 
                       duration: Optional[float] = None) -> bool:
    """
    Validate time range parameters.
    
    Args:
        start_time: Start time in seconds
        end_time: End time in seconds (optional)
        duration: Duration in seconds (optional)
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If time parameters are invalid
    """
    if start_time < 0:
        raise ValueError(f"Start time cannot be negative, got {start_time}")
    
    if end_time is not None:
        if end_time < 0:
            raise ValueError(f"End time cannot be negative, got {end_time}")
        if end_time <= start_time:
            raise ValueError(f"End time ({end_time}) must be greater than start time ({start_time})")
    
    if duration is not None:
        if duration <= 0:
            raise ValueError(f"Duration must be positive, got {duration}")
        if end_time is not None and abs((start_time + duration) - end_time) > 0.001:
            raise ValueError(f"Duration ({duration}) inconsistent with start ({start_time}) and end ({end_time}) times")
    
    return True


def validate_bpm(bpm: float) -> bool:
    """
    Validate BPM value.
    
    Args:
        bpm: Beats per minute
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If BPM is invalid
    """
    if not isinstance(bpm, (int, float)):
        raise ValueError(f"BPM must be a number, got {type(bpm)}")
    
    if not (20 <= bpm <= 300):
        raise ValueError(f"BPM must be between 20-300, got {bpm}")
    
    return True


def validate_fixture_id(fixture_id: str, available_fixtures: List[str]) -> bool:
    """
    Validate fixture ID against available fixtures.
    
    Args:
        fixture_id: Fixture identifier
        available_fixtures: List of available fixture IDs
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If fixture ID is invalid
    """
    if not isinstance(fixture_id, str):
        raise ValueError(f"Fixture ID must be a string, got {type(fixture_id)}")
    
    if not fixture_id.strip():
        raise ValueError("Fixture ID cannot be empty")
    
    if fixture_id not in available_fixtures:
        raise ValueError(f"Fixture '{fixture_id}' not found in available fixtures: {available_fixtures}")
    
    return True


def validate_preset_name(preset_name: str, available_presets: List[str]) -> bool:
    """
    Validate preset name against available presets.
    
    Args:
        preset_name: Preset name
        available_presets: List of available preset names
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If preset name is invalid
    """
    if not isinstance(preset_name, str):
        raise ValueError(f"Preset name must be a string, got {type(preset_name)}")
    
    if not preset_name.strip():
        raise ValueError("Preset name cannot be empty")
    
    if preset_name not in available_presets:
        raise ValueError(f"Preset '{preset_name}' not found in available presets: {available_presets}")
    
    return True


def validate_session_id(session_id: str) -> bool:
    """
    Validate AI conversation session ID.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If session ID is invalid
    """
    if not isinstance(session_id, str):
        raise ValueError(f"Session ID must be a string, got {type(session_id)}")
    
    if not session_id.strip():
        raise ValueError("Session ID cannot be empty")
    
    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not all(c.isalnum() or c in '_-' for c in session_id):
        raise ValueError(f"Session ID contains invalid characters: {session_id}")
    
    return True


def validate_confidence_score(confidence: float) -> bool:
    """
    Validate confidence score.
    
    Args:
        confidence: Confidence value (0.0-1.0)
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If confidence is out of range
    """
    if not isinstance(confidence, (int, float)):
        raise ValueError(f"Confidence must be a number, got {type(confidence)}")
    
    if not (0.0 <= confidence <= 1.0):
        raise ValueError(f"Confidence must be between 0.0-1.0, got {confidence}")
    
    return True
