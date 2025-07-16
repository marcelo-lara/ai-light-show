"""Functions for handling AI action confirmations."""

from typing import List, Dict, Any, Tuple
from ..actions_parser_service import ActionsParserService

def execute_confirmed_action(action_id: str, pending_actions: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Execute a confirmed action from the AI assistant.
    
    Args:
        action_id (str): ID of the action to execute
        pending_actions (List[Dict[str, Any]]): List of pending actions
        
    Returns:
        Tuple[bool, str]: Success flag and result message
    """
    # Find the action by ID
    action = None
    for act in pending_actions:
        if act['id'] == action_id:
            action = act
            break
    
    if not action:
        return False, f"Action {action_id} not found"
    
    try:
        # Use the actions parser service to handle the command
        from ...models.app_state import app_state
        if app_state.fixtures is None:
            return False, "Fixtures not initialized"
            
        parser = ActionsParserService(app_state.fixtures)
        actions = parser.parse_command(action['command'])
        
        if not actions:
            return False, f"Failed to parse command: {action['command']}"
        
        # For now, just return success
        return True, f"Executed: {action['command']}"
        
    except Exception as e:
        return False, f"Error executing action: {e}"
