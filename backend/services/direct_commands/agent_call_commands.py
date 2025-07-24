"""
Agent Call Commands

Handlers for direct agent execution commands.
"""
from typing import Dict, Any, Tuple, Optional
from .base_command import BaseCommandHandler


class CallAgentCommandHandler(BaseCommandHandler):
    """Handler for calling agents directly."""
    
    def matches(self, command: str) -> bool:
        """Check if this handler can process the command."""
        return command.lower().startswith("call ")
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle agent call commands."""
        # Extract agent name from command
        parts = command.split()
        if len(parts) < 2:
            return False, "Usage: call <agent_name> [parameters]", None
        
        agent_name = parts[1].lower()
        
        if agent_name == "lightingplanner":
            return await self._call_lighting_planner(command, websocket)
        else:
            return False, f"Unknown agent: {agent_name}. Available agents: lightingPlanner", None
    
    async def _call_lighting_planner(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Execute the lighting planner agent."""
        try:
            from backend.services.agents import LightingPlannerAgent
            from backend.services.agents.lighting_planner import PipelineState
            from backend.models.app_state import app_state
            
            # Check if we have a current song
            if not app_state.current_song:
                return False, "No song is currently loaded. Load a song first.", None
            
            # Create a test segment from the current song
            song = app_state.current_song
            
            # Get song duration safely
            try:
                song_duration = getattr(song, 'duration', None) or 30.0
            except AttributeError:
                song_duration = 30.0
            
            segment = {
                "start": 0.0,
                "end": min(30.0, song_duration),
                "name": "Test Segment"
            }
            
            # Default context if not provided
            context_summary = "Test lighting context for direct agent call"
            
            # Create properly typed pipeline state
            pipeline_state: PipelineState = {
                "segment": segment,
                "context_summary": context_summary,
                "actions": [],
                "dmx": []
            }
            
            # Execute the agent
            agent = LightingPlannerAgent()
            result = agent.run(pipeline_state)
            
            actions = result.get("actions", [])
            
            return True, f"✅ LightingPlanner executed successfully. Generated {len(actions)} actions.", {
                "actions": actions,
                "segment": segment
            }
            
        except Exception as e:
            return False, f"Error calling LightingPlanner: {str(e)}", None
