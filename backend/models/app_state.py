"""Application state management for the AI Light Show system."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from fastapi import WebSocket

from backend.services.dmx.dmx_canvas import DmxCanvas
from ..config import SONGS_DIR, FIXTURES_FILE
from ..models.fixtures import FixturesListModel


@dataclass
class AppState:
    """Central application state management."""

    # DMX Canvas (must be created first)
    dmx_canvas: DmxCanvas = field(default_factory=DmxCanvas)
    
    # Fixture management (depends on dmx_canvas)
    fixtures: Optional[FixturesListModel] = field(default=None)

    # Fixture and lighting configuration
    fixture_config: List[Dict[str, Any]] = field(default_factory=list)
    fixture_presets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Song management
    current_song_file: Optional[str] = None
    current_song: Optional[Any] = None  # SongMetadata object
    song_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # WebSocket connections
    websocket_clients: List[WebSocket] = field(default_factory=list)
    
    # Cached services to avoid re-initialization
    _actions_parser_service: Optional[Any] = None
    _actions_service: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize fixtures after dmx_canvas is created."""
        if self.fixtures is None:
            self.fixtures = FixturesListModel(
                fixtures_config_file=FIXTURES_FILE, 
                dmx_canvas=self.dmx_canvas, 
                debug=True
            )
            # Invalidate service cache after fixtures are initialized
            self.invalidate_service_cache()
    
    def add_client(self, websocket: WebSocket) -> None:
        """Add a WebSocket client."""
        self.websocket_clients.append(websocket)
    
    def remove_client(self, websocket: WebSocket) -> None:
        """Remove a WebSocket client."""
        if websocket in self.websocket_clients:
            self.websocket_clients.remove(websocket)
    
    def get_actions_parser_service(self):
        """Get cached ActionsParserService or create new one if needed."""
        if self._actions_parser_service is None and self.fixtures is not None:
            from ..services.actions_parser_service import ActionsParserService
            self._actions_parser_service = ActionsParserService(self.fixtures, debug=True)
        return self._actions_parser_service
    
    def get_actions_service(self):
        """Get cached ActionsService or create new one if needed."""
        if self._actions_service is None and self.fixtures is not None and self.dmx_canvas is not None:
            from ..services.actions_service import ActionsService
            self._actions_service = ActionsService(self.fixtures, self.dmx_canvas, debug=True)
        return self._actions_service
    
    def invalidate_service_cache(self):
        """Invalidate cached services when fixtures or canvas change."""
        self._actions_parser_service = None
        self._actions_service = None
    
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
