"""
Core utilities and shared functionality for the AI Light Show backend.
"""

from .time_utils import beats_to_seconds, seconds_to_beats, ms_to_seconds
from .validation import validate_dmx_channel, validate_dmx_value, validate_time_range
from .exceptions import DMXError, AudioProcessingError, AIServiceError

__all__ = [
    'beats_to_seconds',
    'seconds_to_beats', 
    'ms_to_seconds',
    'validate_dmx_channel',
    'validate_dmx_value',
    'validate_time_range',
    'DMXError',
    'AudioProcessingError',
    'AIServiceError'
]
