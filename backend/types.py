"""
Type definitions for the AI Light Show backend.

This module provides comprehensive type hints to improve code analysis,
IntelliSense support, and reduce token consumption through better organization.
"""

from typing import TypedDict, Literal, Optional, List, Dict, Any, Union, Protocol, Callable
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Core Data Types
# ============================================================================

class FixtureType(str, Enum):
    """Supported fixture types."""
    PARCAN = "parcan"
    MOVING_HEAD = "moving_head"
    LED_STRIP = "led_strip"
    STROBE = "strobe"
    LASER = "laser"


class EffectType(str, Enum):
    """Available lighting effects."""
    FLASH = "flash"
    FADE = "fade"
    STROBE = "strobe"
    CHASE = "chase"
    RAINBOW = "rainbow"
    PULSE = "pulse"


class CommandType(str, Enum):
    """AI command types."""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    CLEAR = "clear"


# ============================================================================
# DMX and Hardware Types
# ============================================================================

@dataclass
class DMXChannel:
    """DMX channel configuration."""
    channel: int
    value: int
    fixture_id: str
    parameter: str


class DMXUniverse(TypedDict):
    """DMX universe state."""
    channels: List[int]  # 512 channels
    last_update: float
    fps: int


class ArtNetConfig(TypedDict):
    """Art-Net configuration."""
    ip: str
    port: int
    universe: int


# ============================================================================
# Fixture and Preset Types
# ============================================================================

class FixtureChannel(TypedDict):
    """Individual fixture channel definition."""
    name: str
    channel: int
    default: int
    min_val: int
    max_val: int


class FixtureConfig(TypedDict):
    """Complete fixture configuration."""
    id: str
    name: str
    type: FixtureType
    start_channel: int
    channels: List[FixtureChannel]
    position: Optional[Dict[str, float]]


class PresetConfig(TypedDict):
    """Lighting preset configuration."""
    name: str
    fixture_type: FixtureType
    channels: Dict[str, int]
    description: Optional[str]


class ChaserTemplate(TypedDict):
    """Chaser effect template."""
    name: str
    steps: List[Dict[str, Any]]
    duration_beats: float
    loop: bool


# ============================================================================
# Audio Analysis Types
# ============================================================================

class AudioFeatures(TypedDict):
    """Audio analysis features."""
    bpm: float
    key: str
    energy: float
    danceability: float
    valence: float


class BeatInfo(TypedDict):
    """Beat detection information."""
    times: List[float]
    confidence: List[float]
    bpm: float


class ChordProgression(TypedDict):
    """Chord progression data."""
    time: float
    chord: str
    confidence: float


class SongSection(TypedDict):
    """Song structure section."""
    name: str
    start_time: float
    end_time: float
    confidence: float


class DrumPattern(TypedDict):
    """Drum pattern detection."""
    kick: List[float]
    snare: List[float]
    hihat: List[float]
    confidence: float


# ============================================================================
# AI and LLM Types
# ============================================================================

ModelName = Literal["mistral", "llama2", "codellama", "phi"]

class OllamaMessage(TypedDict):
    """Ollama chat message."""
    role: Literal["system", "user", "assistant"]
    content: str


class OllamaResponse(TypedDict):
    """Ollama API response."""
    message: OllamaMessage
    done: bool
    created_at: str
    model: str


class ActionProposal(TypedDict):
    """AI action proposal."""
    id: str
    command: str
    description: str
    confidence: float
    parameters: Dict[str, Any]


class ConversationSession(TypedDict):
    """AI conversation session."""
    session_id: str
    messages: List[OllamaMessage]
    current_song: Optional[str]
    last_activity: float


# ============================================================================
# Cue and Timeline Types
# ============================================================================

class CueStep(TypedDict):
    """Individual cue step."""
    time: float
    fixture_id: str
    channels: Dict[str, int]
    duration: Optional[float]


class LightingCue(TypedDict):
    """Complete lighting cue."""
    id: str
    name: str
    start_time: float
    duration: float
    steps: List[CueStep]
    effect_type: EffectType
    parameters: Dict[str, Any]


class Timeline(TypedDict):
    """Lighting timeline."""
    cues: List[LightingCue]
    bpm: float
    duration: float
    fps: int


# ============================================================================
# Song and Metadata Types
# ============================================================================

class SongMetadata(TypedDict):
    """Complete song metadata."""
    filename: str
    title: Optional[str]
    artist: Optional[str]
    duration: float
    bpm: float
    key: str
    audio_features: AudioFeatures
    beats: BeatInfo
    sections: List[SongSection]
    chords: List[ChordProgression]
    drums: Optional[DrumPattern]


# ============================================================================
# API and Service Types
# ============================================================================

class APIResponse(TypedDict):
    """Standard API response."""
    success: bool
    message: str
    data: Optional[Any]


class WebSocketMessage(TypedDict):
    """WebSocket message format."""
    type: str
    data: Any
    timestamp: float


class HealthStatus(TypedDict):
    """Service health status."""
    service: str
    status: Literal["healthy", "unhealthy", "degraded"]
    details: Optional[str]
    timestamp: float


# ============================================================================
# Protocol Interfaces
# ============================================================================

class AudioProcessor(Protocol):
    """Protocol for audio processing services."""
    
    def analyze_audio(self, file_path: str) -> AudioFeatures:
        """Analyze audio file and extract features."""
        ...
    
    def detect_beats(self, file_path: str) -> BeatInfo:
        """Detect beats in audio file."""
        ...


class LightingController(Protocol):
    """Protocol for lighting control services."""
    
    def set_channel(self, channel: int, value: int) -> bool:
        """Set DMX channel value."""
        ...
    
    def send_universe(self, universe: List[int]) -> None:
        """Send complete DMX universe."""
        ...


class AIClient(Protocol):
    """Protocol for AI service clients."""
    
    async def generate_response(
        self, 
        prompt: str, 
        model: ModelName = "mistral",
        session_id: str = "default"
    ) -> str:
        """Generate AI response."""
        ...
    
    async def stream_response(
        self,
        prompt: str,
        callback: Callable[[str], None],
        model: ModelName = "mistral",
        session_id: str = "default"
    ) -> None:
        """Stream AI response with callback."""
        ...


# ============================================================================
# Configuration Types
# ============================================================================

class DatabaseConfig(TypedDict):
    """Database configuration."""
    url: str
    pool_size: int
    timeout: float


class ServerConfig(TypedDict):
    """Server configuration."""
    host: str
    port: int
    debug: bool
    cors_origins: List[str]


class AIConfig(TypedDict):
    """AI service configuration."""
    base_url: str
    model: ModelName
    timeout: float
    max_tokens: int


class AppConfig(TypedDict):
    """Complete application configuration."""
    server: ServerConfig
    database: DatabaseConfig
    ai: AIConfig
    dmx: ArtNetConfig
    fixtures: List[FixtureConfig]
    presets: List[PresetConfig]


# ============================================================================
# Utility Types
# ============================================================================

TimeReference = Union[float, str]  # Seconds or "verse", "chorus", etc.
ChannelValue = int  # 0-255 DMX value
BeatPosition = float  # Beat position in song
