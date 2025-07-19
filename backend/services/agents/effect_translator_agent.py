"""
Agent for interacting with the 'effect_translator' LLM model.
"""

from ..ollama.ollama_api import query_ollama

class EffectTranslatorAgent:
    def __init__(self):
        self.model = 'effect_translator'

    def translate_effect(self, prompt: str, **kwargs):
        response = query_ollama(prompt, model=self.model, **kwargs)
        return self.parse_response(response)

    def parse_response(self, response):
        # Implement model-specific parsing logic here
        return response
