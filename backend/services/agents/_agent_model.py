from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

@dataclass
class AgentState:
    """Dataclass to represent the state of an agent."""
    status: str = "idle"
    progress: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AgentModel:
    """Base class for all agent models."""
    def __init__(self, agent_name: str, model_name: str, agent_alisas: Optional[str] = None):
        self.agent_name = agent_name
        self.model_name = model_name
        self.agent_alisas = agent_alisas or agent_alisas
        self.state = AgentState()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent model on the input data."""
        raise NotImplementedError("AgentModel subclasses must implement the run method.")

    def _call_ollama(self, prompt: str) -> str:
        """Call the Ollama API with the given prompt."""
        # This method should be implemented to interact with the Ollama API
        raise NotImplementedError("AgentModel subclasses must implement the _call_ollama method.")

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build a prompt for the agent model using Jinja2 templates from the prompts directory."""
        prompts_dir = Path(__file__).parent / "prompts"
        jinja_env = Environment(
            loader=FileSystemLoader(prompts_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        template = jinja_env.get_template(f"{self.agent_name}.j2")
        return template.render(context)