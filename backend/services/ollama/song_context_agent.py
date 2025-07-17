"""
Agent for interacting with the 'song_context' LLM model.
"""

from .ollama_api import query_ollama

class SongContextAgent:
    def __init__(self):
        # Initialize with model name or config if needed
        self.model = 'song_context'

    def get_context(self, prompt: str, **kwargs):
        # Call the LLM server for song context
        response = query_ollama(prompt, model=self.model, **kwargs)
        return self.parse_response(response)

    def parse_response(self, response):
        # Implement model-specific parsing logic here
        return response
