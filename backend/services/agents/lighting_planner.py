"""
LangGraph Lighting Planner Agent
"""

from ..ollama.ollama_api import query_ollama

class LightingPlannerAgent:
    def __init__(self, model: str = "mixtral"):
        self.model = model
    def run(self, state):
        # Implement lighting planning logic here
        return state
