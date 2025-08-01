"""Application state management for the AI Light Show system."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from fastapi import WebSocket
from pathlib import Path
import asyncio
from datetime import datetime

from backend.services.dmx.dmx_canvas import DmxCanvas
from shared.models.song_metadata import SongMetadata
from ..config import SONGS_DIR, FIXTURES_FILE
from ..models.fixtures import FixturesListModel


@dataclass
class TaskState:
    """State tracking for background tasks."""
    task_id: str
    song_name: str
    operation: str
    status: str  # "running", "completed", "error"
    progress: int = 0
    current: int = 0
    total: int = 0
    message: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    task: Optional[asyncio.Task] = None


@dataclass
class AppState:
    """Central application state management."""

    # Logs folder path
    logs_folder: Path = Path("/app/logs") if Path("/app/logs").exists() else Path(__file__).parent.parent / "logs"

    # DMX Canvas - Using singleton instance
    dmx_canvas: DmxCanvas = field(init=False)
    
    # Fixture management (depends on dmx_canvas)
    fixtures: Optional[FixturesListModel] = field(default=None)
    
    # Song management
    current_song_file: Optional[str] = None
    current_song: SongMetadata = SongMetadata()  # SongMetadata object
    song_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # WebSocket connections
    websocket_clients: List[WebSocket] = field(default_factory=list)
    
    # Background task tracking
    background_tasks: Dict[str, TaskState] = field(default_factory=dict)
    
    # Cached services to avoid re-initialization
    _actions_parser_service: Optional[Any] = None
    _actions_service: Optional[Any] = None
    
    def __post_init__(self):
        """Initialize DMX Canvas singleton and fixtures."""
        # Initialize the DMX Canvas singleton instance
        self.dmx_canvas = DmxCanvas.get_instance()
        
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
            from ..services.dmx.actions_parser_service import ActionsParserService
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
    
    def reset_dmx_canvas(self, fps: int = 44, duration: float = 300.0, debug: bool = False) -> DmxCanvas:
        """
        Reset the DMX Canvas singleton with new parameters.
        
        This method should be used when loading a new song with different duration
        or when canvas parameters need to be changed.
        
        Args:
            fps (int): Frames per second for the timeline. Defaults to 44.
            duration (float): Total duration of the timeline in seconds. Defaults to 300.0.
            debug (bool): Enable debug logging. Defaults to False.
            
        Returns:
            DmxCanvas: The reset singleton instance.
        """
        # Reset the singleton with new parameters
        self.dmx_canvas = DmxCanvas.reset_instance(fps=fps, duration=duration, debug=debug)
        
        # Update fixtures with new canvas
        if self.fixtures is not None:
            self.fixtures.dmx_canvas = self.dmx_canvas
        
        # Invalidate cached services since canvas has changed
        self.invalidate_service_cache()
        
        print(f"🔄 DMX Canvas reset: {duration}s duration at {fps} FPS")
        return self.dmx_canvas
    
    def create_background_task(self, task_id: str, song_name: str, operation: str, total: int = 0) -> TaskState:
        """Create a new background task state."""
        task_state = TaskState(
            task_id=task_id,
            song_name=song_name,
            operation=operation,
            status="running",
            total=total
        )
        self.background_tasks[task_id] = task_state
        return task_state
    
    def update_task_progress(self, task_id: str, progress: int, current: int, message: str = "", error: bool = False):
        """Update progress for a background task."""
        if task_id in self.background_tasks:
            task_state = self.background_tasks[task_id]
            task_state.progress = progress
            task_state.current = current
            task_state.message = message
            if error:
                task_state.status = "error"
                task_state.error = message
    
    def complete_task(self, task_id: str, result: Any = None, error: Optional[str] = None):
        """Mark a background task as completed."""
        if task_id in self.background_tasks:
            task_state = self.background_tasks[task_id]
            task_state.completed_at = datetime.now()
            task_state.result = result
            if error:
                task_state.status = "error"
                task_state.error = error
            else:
                task_state.status = "completed"
                task_state.progress = 100
    
    def get_task_state(self, task_id: str) -> Optional[TaskState]:
        """Get the state of a background task."""
        return self.background_tasks.get(task_id)
    
    def get_tasks_for_song(self, song_name: str) -> List[TaskState]:
        """Get all tasks for a specific song."""
        return [task for task in self.background_tasks.values() if task.song_name == song_name]
    
    def broadcast_to_clients(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSocket clients."""
        import asyncio
        for client in self.websocket_clients[:]:  # Copy list to avoid modification during iteration
            try:
                # Use create_task to avoid blocking
                asyncio.create_task(client.send_json(message))
            except Exception:
                # Remove disconnected clients
                self.remove_client(client)

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
