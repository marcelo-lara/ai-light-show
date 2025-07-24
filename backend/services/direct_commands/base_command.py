"""
Base command handler class for direct commands.
"""
from typing import Dict, Any, Tuple, Optional
from abc import ABC, abstractmethod


class BaseCommandHandler(ABC):
    """Base class for all command handlers."""
    
    def __init__(self):
        """Initialize the command handler."""
        pass
    
    @abstractmethod
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Handle a command.
        
        Args:
            command (str): The command text (without # prefix)
            websocket: WebSocket connection (optional)
            
        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: 
                - Success flag
                - Message to return to the user
                - Additional data (if any)
        """
        pass
    
    @abstractmethod
    def matches(self, command: str) -> bool:
        """
        Check if this handler can process the given command.
        
        Args:
            command (str): The command text (without # prefix)
            
        Returns:
            bool: True if this handler can process the command
        """
        pass
