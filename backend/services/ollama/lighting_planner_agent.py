"""
Agent for interacting with the 'lighting_planner' LLM model.
"""

from .ollama_api import query_ollama

class LightingPlannerAgent:
    def __init__(self):
        self.model = 'lighting_planner'

    def plan_lighting(self, prompt: str, **kwargs):
        response = query_ollama(prompt, model=self.model, **kwargs)
        return self.parse_response(response)

    def parse_response(self, response):
        # Implement model-specific parsing logic here
        return response
