"""Application state management for the AI Light Show system."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from fastapi import WebSocket

from backend.services.dmx_canvas import DmxCanvas
from ..config import SONGS_DIR, FIXTURES_FILE
from ..models.fixtures_model import FixturesModel


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

    # Fixture management
    fixtures = FixturesModel(fixtures_config_file=FIXTURES_FILE, debug=True)
    dmx_canvas = DmxCanvas()

    # Fixture and lighting configuration
    fixture_config: List[Dict[str, Any]] = field(default_factory=list)
    fixture_presets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Song management
    current_song_file: Optional[str] = None
    current_song: Optional[Any] = None  # SongMetadata object
    song_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Playback state
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
    
    # List of available songs in the songs folder
    def get_songs_list(self) -> List[str]:
        """
        Returns a list of available songs in the songs folder.
        """
        from pathlib import Path

        # Ensure the SONGS_DIR exists
        if not SONGS_DIR.exists():
            return []

        # List all mp3 files in the SONGS_DIR
        songs_list = list(SONGS_DIR.glob("*.mp3"))
        
        # Return a list of song names without the file extension
        return [song.stem for song in songs_list if song.is_file()]

# Global application state instance
app_state = AppState()
