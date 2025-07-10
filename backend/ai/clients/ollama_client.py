"""
Main Ollama client module - provides the public API by importing from specialized modules.

This module serves as the main entry point for Ollama functionality, importing
and exposing functions from the specialized modules:
- ollama_health: Health checking and status
- ollama_conversation: Conversation history management  
- ollama_instructions: System instruction generation
- ollama_actions: Action proposal and execution
- ollama_api: Core API communication
"""

# Health checking
from .ollama_health import (
    check_ollama_health,
    get_ollama_status
)

# Conversation management
from .ollama_conversation import (
    clear_conversation,
    get_active_sessions,
    get_conversation_history,
    reset_conversation_with_system,
    refresh_system_configuration,
    set_current_song,
    clear_current_song,
    get_current_song
)

# System instructions and configuration
from .ollama_instructions import (
    generate_system_instructions,
    get_system_message,
    get_current_fixtures,
    get_current_presets,
    get_current_chasers
)

# Action processing
from .ollama_actions import (
    extract_action_proposals,
    execute_confirmed_action
)

# Core API communication
from .ollama_api import (
    query_ollama_mistral,
    query_ollama_mistral_streaming,
    query_ollama_with_actions
)

# Re-export all functions for backward compatibility
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
