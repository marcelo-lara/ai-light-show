"""
Custom exceptions for the AI Light Show backend.

Provides specific exception types for different error conditions
to improve error handling and debugging.
"""

from typing import Optional, Any


class AILightShowError(Exception):
    """Base exception for all AI Light Show errors."""
    pass


class DMXError(AILightShowError):
    """Raised when DMX-related operations fail."""
    
    def __init__(self, message: str, channel: Optional[int] = None, value: Optional[int] = None):
        super().__init__(message)
        self.channel = channel
        self.value = value


class AudioProcessingError(AILightShowError):
    """Raised when audio processing operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, stage: Optional[str] = None):
        super().__init__(message)
        self.file_path = file_path
        self.stage = stage


class AIServiceError(AILightShowError):
    """Raised when AI service operations fail."""
    
    def __init__(self, message: str, service: Optional[str] = None, model: Optional[str] = None):
        super().__init__(message)
        self.service = service
        self.model = model


class FixtureConfigError(AILightShowError):
    """Raised when fixture configuration is invalid."""
    
    def __init__(self, message: str, fixture_id: Optional[str] = None):
        super().__init__(message)
        self.fixture_id = fixture_id


class PresetError(AILightShowError):
    """Raised when preset operations fail."""
    
    def __init__(self, message: str, preset_name: Optional[str] = None):
        super().__init__(message)
        self.preset_name = preset_name


class CueError(AILightShowError):
    """Raised when cue operations fail."""
    
    def __init__(self, message: str, cue_id: Optional[str] = None, time: Optional[float] = None):
        super().__init__(message)
        self.cue_id = cue_id
        self.time = time


class TimelineError(AILightShowError):
    """Raised when timeline operations fail."""
    
    def __init__(self, message: str, current_time: Optional[float] = None):
        super().__init__(message)
        self.current_time = current_time


class ValidationError(AILightShowError):
    """Raised when validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message)
        self.field = field
        self.value = value


class ConfigurationError(AILightShowError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message)
        self.config_key = config_key


class NetworkError(AILightShowError):
    """Raised when network operations fail."""
    
    def __init__(self, message: str, host: Optional[str] = None, port: Optional[int] = None):
        super().__init__(message)
        self.host = host
        self.port = port


class SongAnalysisError(AudioProcessingError):
    """Raised when song analysis fails."""
    
    def __init__(self, message: str, song_file: Optional[str] = None, analysis_type: Optional[str] = None):
        super().__init__(message, song_file, analysis_type)
        self.analysis_type = analysis_type


class ModelLoadError(AIServiceError):
    """Raised when ML model loading fails."""
    
    def __init__(self, message: str, model_path: Optional[str] = None, model_type: Optional[str] = None):
        super().__init__(message, "model_loader", model_type)
        self.model_path = model_path
        self.model_type = model_type
