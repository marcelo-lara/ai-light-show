"""WebSocket handlers package."""

from .sync_handler import handle_sync, handle_blackout
from .song_handler import handle_load_song, handle_save_arrangement, handle_save_key_moments, handle_analyze_song
from .dmx_handler import handle_set_dmx
from .ai_handler import handle_user_prompt
from .pipeline_handler import handle_run_lighting_pipeline
from .agent_handler import handle_run_agent

__all__ = [
    'handle_sync',
    'handle_blackout',
    'handle_load_song',
    'handle_save_arrangement',
    'handle_save_key_moments',
    'handle_analyze_song',
    'handle_set_dmx',
    'handle_user_prompt',
    'handle_run_lighting_pipeline',
    'handle_run_agent',
]
