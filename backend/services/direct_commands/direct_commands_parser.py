"""
Direct Commands Parser

This service parses direct action commands sent by the user through ChatAssistant.
Commands start with #action and bypass the LLM processing.
"""
from typing import Dict, Any, Tuple, List, Optional

from .base_command import BaseCommandHandler
from .help_command import HelpCommandHandler
from .tasks_command import TasksCommandHandler
from .analyze_commands import AnalyzeCommandHandler, AnalyzeContextCommandHandler
from .agent_call_commands import CallAgentCommandHandler
from .action_commands import (
    RenderCommandHandler, 
    ClearCommandHandler, 
    AddCommandHandler, 
    DirectActionCommandHandler
)
from .light_plan_commands import (
    CreateLightPlanCommandHandler,
    DeleteLightPlanCommandHandler,
    ResetLightPlansCommandHandler,
    ListLightPlansCommandHandler
)


class DirectCommandsParser:
    """Parser for direct action commands from ChatAssistant."""
    
    def __init__(self):
        """Initialize the direct commands parser with all command handlers."""
        self.handlers: List[BaseCommandHandler] = [
            HelpCommandHandler(),
            TasksCommandHandler(),
            AnalyzeContextCommandHandler(),  # Must come before AnalyzeCommandHandler
            AnalyzeCommandHandler(),
            CallAgentCommandHandler(),
            CreateLightPlanCommandHandler(),
            DeleteLightPlanCommandHandler(),
            ResetLightPlansCommandHandler(),
            ListLightPlansCommandHandler(),
            RenderCommandHandler(),
            ClearCommandHandler(),
            AddCommandHandler(),
            DirectActionCommandHandler(),  # Keep this last as it's the fallback
        ]
    
    async def parse_command(self, command_text: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Parse a direct command and execute it. Async to allow calling async handlers.
        
        Args:
            command_text (str): The command text from the user (starts with #action)
            
        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: 
                - Success flag
                - Message to return to the user
                - Additional data (if any)
        """
        # Accept both #action and # as prefix
        command = command_text.lstrip("#").strip()
        command = command.replace("action", "", 1).strip() if command.lower().startswith("action") else command

        # Find the first handler that matches this command
        for handler in self.handlers:
            if handler.matches(command):
                try:
                    return await handler.handle(command)
                except Exception as e:
                    return False, f"Error processing command '{command}': {str(e)}", None
        
        # This should never happen since DirectActionCommandHandler always matches
        return False, f"No handler found for command: {command}", None
