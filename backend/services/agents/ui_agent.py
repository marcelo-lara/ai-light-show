"""
UI Agent

This agent routes user intentions to the appropriate agents to fulfill their requests.
"""

from typing import Optional
from ._agent_model import AgentModel

class UIAgent(AgentModel):
    """
    UI Agent model that routes user requests to appropriate sub-agents.
    sub-agensts are:
    
    """

    def __init__(self, agent_name: str = "ui_agent", model_name: str = "cogito:8b", agent_aliases: Optional[str] = "ui"):
        super().__init__(agent_name, model_name, agent_aliases)
