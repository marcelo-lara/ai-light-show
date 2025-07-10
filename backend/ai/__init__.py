"""
AI module for the AI Light Show backend.

Provides a unified interface to AI services, machine learning models,
and audio processing capabilities with improved organization and type hints.
"""

# Import from reorganized submodules
from .clients import *
from .ml import *
from .processing import *

# Import remaining modules in the ai directory
from .arrangement_guess import guess_arrangement_using_drum_patterns, guess_arrangement
from .cue_interpreter import CueInterpreter

__all__ = [
    # AI Clients (Ollama, etc.)
    'check_ollama_health',
    'get_ollama_status',
    'clear_conversation',
    'get_active_sessions', 
    'get_conversation_history',
    'reset_conversation_with_system',
    'refresh_system_configuration',
    'set_current_song',
    'clear_current_song',
    'get_current_song',
    'generate_system_instructions',
    'get_system_message',
    'get_current_fixtures',
    'get_current_presets',
    'get_current_chasers',
    'extract_action_proposals',
    'execute_confirmed_action',
    'query_ollama_mistral',
    'query_ollama_mistral_streaming',
    'query_ollama_with_actions',
    
    # Machine Learning
    'infer_drums',
    'get_stem_clusters', 
    'get_stem_clusters_with_model',
    'get_model_and_processor',
    
    # Audio Processing
    'noise_gate',
    'extract_stems',
    'extract_with_essentia', 
    'extract_chords_and_align',
    
    # Other AI modules
    'guess_arrangement_using_drum_patterns',
    'guess_arrangement',
    'CueInterpreter'
]
