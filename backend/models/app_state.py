"""Application state management for the AI Light Show system."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class PlaybackState:
    """Manages playback timing and state."""
    is_playing: bool = False
    playback_time: float = 0.0
    start_monotonic: float = 0.0
    last_sent: float = 0.0


@dataclass
class AppState:
    """Central application state management."""
    # Fixture and lighting configuration
    fixture_config: List[Dict[str, Any]] = field(default_factory=list)
    fixture_presets: List[Dict[str, Any]] = field(default_factory=list)
    chasers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Song management
    current_song_file: Optional[str] = None
    current_song: Optional[Any] = None  # SongMetadata object
    song_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timeline and playback
    timeline: List[Any] = field(default_factory=list)
    playback: PlaybackState = field(default_factory=PlaybackState)
    
    # WebSocket connections
    websocket_clients: List[WebSocket] = field(default_factory=list)
    
    def add_client(self, websocket: WebSocket) -> None:
        """Add a WebSocket client."""
        self.websocket_clients.append(websocket)
    
    def remove_client(self, websocket: WebSocket) -> None:
        """Remove a WebSocket client."""
        if websocket in self.websocket_clients:
            self.websocket_clients.remove(websocket)
    


# Global application state instance
app_state = AppState()
