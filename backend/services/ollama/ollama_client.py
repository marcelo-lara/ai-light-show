"""
Simplified Ollama client module - provides basic chat functionality.
"""

# Core API communication
from .ollama_api import query_ollama
from .ollama_streaming import query_ollama_streaming
