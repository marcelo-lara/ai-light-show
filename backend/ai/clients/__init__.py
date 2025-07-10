"""
AI client modules for external services.

Contains clients for various AI services like Ollama, OpenAI, etc.
"""

from .ollama_client import *

__all__ = [
    # Health
    'check_ollama_health',
    'get_ollama_status',
    
    # Conversation
    'clear_conversation',
    'get_active_sessions', 
    'get_conversation_history',
    'reset_conversation_with_system',
    'refresh_system_configuration',
    'set_current_song',
    'clear_current_song',
    'get_current_song',
    
    # Instructions
    'generate_system_instructions',
    'get_system_message',
    'get_current_fixtures',
    'get_current_presets',
    'get_current_chasers',
    
    # Actions
    'extract_action_proposals',
    'execute_confirmed_action',
    
    # API
    'query_ollama_mistral',
    'query_ollama_mistral_streaming',
    'query_ollama_with_actions'
]
