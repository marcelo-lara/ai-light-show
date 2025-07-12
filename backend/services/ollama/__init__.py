"""
Ollama AI service module for the AI Light Show system.

This package provides AI-powered lighting generation and conversation capabilities
using the Ollama local LLM service.

Modules:
- ollama_client: Main client entry point (re-exports from other modules)
- ollama_api: Core API communication with Ollama service
- ollama_health: Health checking and status monitoring
- ollama_conversation: Conversation history and session management
- ollama_instructions: System instruction generation
- ollama_actions: Action proposal extraction and execution
"""

# Import main client for easy access
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
    
    # Actions
    'extract_action_proposals',
    'execute_confirmed_action',
    
    # API
    'query_ollama_mistral',
    'query_ollama_mistral_streaming',
    'query_ollama_with_actions'
]
