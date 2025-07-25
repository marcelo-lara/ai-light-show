"""
Simplified Ollama AI service module for the AI Light Show system.

This package provides AI-powered conversation capabilities
using the Ollama local LLM service.

Modules:
- ollama_client: Main client entry point (re-exports from other modules)
- ollama_api: Core API communication with Ollama service
- ollama_streaming: Streaming functionality for real-time responses
"""

# Import all exports from the client module
from .ollama_api import query_ollama
from .ollama_streaming import query_ollama_streaming

# Define what gets exported from the package
__all__ = [
    'query_ollama',
    'query_ollama_streaming',
]
