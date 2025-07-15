"""
Simplified Ollama AI service module for the AI Light Show system.

This package provides AI-powered conversation capabilities
using the Ollama local LLM service.

Modules:
- ollama_client: Main client entry point (re-exports from other modules)
- ollama_api: Core API communication with Ollama service
- ollama_streaming: Streaming functionality for real-time responses
"""

# Import client functions for easy access
from .ollama_api import query_ollama_mistral
from .ollama_streaming import query_ollama_mistral_streaming

__all__ = [
    # API
    'query_ollama_mistral',
    'query_ollama_mistral_streaming'
]
