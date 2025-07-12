"""Conversation history management for Ollama sessions."""

from typing import Dict, List
from .ollama_instructions import get_system_message

# Store conversation history per user/session (instead of deprecated context)
_conversation_histories = {}


def get_conversation_messages(session_id: str = "default") -> List[Dict]:
    """Get the conversation history messages for a session."""
    return _conversation_histories.get(session_id, [])


def update_conversation_history(session_id: str, messages: List[Dict], assistant_response: str):
    """Update conversation history with assistant response."""
    messages.append({"role": "assistant", "content": assistant_response})
    _conversation_histories[session_id] = messages


def clear_conversation(session_id: str = "default"):
    """Clear conversation history for a session."""
    if session_id in _conversation_histories:
        del _conversation_histories[session_id]


def get_active_sessions():
    """Get list of active conversation sessions."""
    return list(_conversation_histories.keys())


def get_conversation_history(session_id: str = "default"):
    """Get the conversation history for a session."""
    return _conversation_histories.get(session_id, [])


def reset_conversation_with_system(session_id: str = "default"):
    """Reset conversation and start fresh with system message."""
    _conversation_histories[session_id] = [get_system_message(session_id)]


def refresh_system_configuration():
    """Refresh system configuration by reloading fixture data and clearing conversations."""
    # Clear all conversations to apply new configuration
    _conversation_histories.clear()


# Legacy functions for compatibility
def set_current_song(session_id: str, song_info: dict):
    """Legacy function for compatibility - song context now managed by AppState."""
    # Note: Song context is now managed directly through AppState.current_song
    # This function is kept for backward compatibility but does nothing
    # System instructions will automatically reflect AppState.current_song
    pass


def clear_current_song(session_id: str = "default"):
    """Legacy function for compatibility - song context now managed by AppState."""
    # Note: Song context is now managed directly through AppState.current_song
    # This function is kept for backward compatibility but does nothing
    # To clear the current song, set AppState.current_song = None
    pass


def get_current_song(session_id: str = "default"):
    """Get the current song context from AppState."""
    from ...models.app_state import app_state
    
    if app_state.current_song:
        return {
            'title': app_state.current_song.title,
            'genre': app_state.current_song.genre,
            'bpm': app_state.current_song.bpm,
            'duration': app_state.current_song.duration,
            'beats': len(app_state.current_song.beats),
            'arrangement_sections': len(app_state.current_song.arrangement) if app_state.current_song.arrangement else 0
        }
    return {}
