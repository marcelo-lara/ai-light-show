from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Callable
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
    def __init__(self, agent_name: str, model_name: str, agent_alisas: Optional[str] = None, debug: bool = False):
        self.agent_name = agent_name
        self.model_name = model_name
        self.agent_alisas = agent_alisas or agent_alisas
        self.state = AgentState()
        self.debug = debug

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent model on the input data."""
        raise NotImplementedError("AgentModel subclasses must implement the run method.")

    def _call_ollama(self, prompt: str, context: Optional[str] = None, callback: Optional[Callable] = None, **kwargs) -> str:
        """Call the Ollama API with the given prompt."""
        # Import here to avoid circular imports
        from ..ollama import query_ollama_streaming
        import asyncio
        
        # Create a new event loop if none exists (for sync usage)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Call the async streaming function
        return loop.run_until_complete(
            query_ollama_streaming(
                prompt=prompt,
                model=self.model_name,
                context=context,
                callback=callback,
                **kwargs
            )
        )

    async def _call_ollama_async(self, prompt: str, context: Optional[str] = None, callback: Optional[Callable] = None, **kwargs) -> str:
        """Call the Ollama API asynchronously with the given prompt."""
        from ..ollama import query_ollama_streaming
        
        if self.debug:
            """Save the prompt and context to logs for debugging"""
            from ...models.app_state import app_state
            log_file = Path(app_state.logs_folder) / f"{self.agent_name}_debug.log"
            print(f"Debug log file: {log_file}")
            app_state.logs_folder.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a") as f:
                f.write(f"Prompt: {prompt}\nContext: {context}\n\n")

        return await query_ollama_streaming(
            prompt=prompt,
            model=self.model_name,
            context=context,
            callback=callback,
            **kwargs
        )

    def _build_context(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build the context for the agent model from the input data."""
        # This method should be implemented to interact with the Ollama API
        raise NotImplementedError("AgentModel subclasses must implement the _build_context method.")

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

    async def health(self) -> tuple[bool, str]:
        """Check if the agent and its underlying services are available and return status."""
        try:
            # Test that we can build context (this tests underlying dependencies)
            # We'll catch expected errors that indicate the agent is working but dependencies are missing
            try:
                test_context = self._build_context({})
            except ValueError as ve:
                if "No song is currently loaded" in str(ve):
                    # This is expected when no song is loaded, but it means the agent setup is working
                    return True, f"Agent '{self.agent_name}' is ready (no song loaded)"
                else:
                    raise ve
            except AttributeError as ae:
                # Handle case where dependencies exist but are not properly initialized
                if "_title" in str(ae) or "_beats" in str(ae) or "song" in str(ae).lower():
                    return True, f"Agent '{self.agent_name}' is ready (dependencies not fully loaded)"
                else:
                    raise ae
            
            # If we got here, dependencies are loaded and context built successfully
            return True, f"Agent '{self.agent_name}' is ready"
            
        except ConnectionError:
            return False, f"Cannot connect to Ollama service. Please ensure Ollama is running on http://llm-service:11434"
        except ValueError as ve:
            if "not found" in str(ve) and "model" in str(ve):
                return False, f"Model '{self.model_name}' not found. Please install it with: ollama pull {self.model_name}"
            else:
                return False, f"Agent '{self.agent_name}' error: {str(ve)}"
        except Exception as e:
            return False, f"Agent '{self.agent_name}' error: {str(e)}"