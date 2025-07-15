"""
Simplified Ollama client module - provides basic chat functionality.
"""

# Core API communication
from .ollama_api import query_ollama_mistral
from .ollama_streaming import query_ollama_mistral_streaming

# Re-export the functions for backward compatibility
__all__ = [
    'query_ollama_mistral',
    'query_ollama_mistral_streaming'
]
