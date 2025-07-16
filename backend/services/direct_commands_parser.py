"""
Direct Commands Parser

This service parses direct action commands sent by the user through ChatAssistant.
Commands start with #action and bypass the LLM processing.
"""
import re
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path

from ..models.app_state import app_state
from ..models.actions_sheet import ActionsSheet, ActionModel
from ..services.actions_service import ActionsService


class DirectCommandsParser:
    """Parser for direct action commands from ChatAssistant."""
    
    def __init__(self):
        """Initialize the direct commands parser."""
        pass
    
    def parse_command(self, command_text: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Parse a direct command and execute it.
        
        Args:
            command_text (str): The command text from the user (starts with #action)
            
        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: 
                - Success flag
                - Message to return to the user
                - Additional data (if any)
        """
        # Strip the #action prefix and any whitespace
        command = command_text.replace("#action", "", 1).strip()
        
        # Get current song
        if not app_state.current_song_file:
            return False, "No song loaded. Please load a song first.", None
        
        song_name = Path(app_state.current_song_file).stem
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        
        # Create actions service
        if app_state.fixtures is None or app_state.dmx_canvas is None:
            return False, "Fixtures or DMX canvas not initialized.", None
            
        actions_service = ActionsService(app_state.fixtures, app_state.dmx_canvas)
        
        # Handle different command types
        if command == "render":
            return self._handle_render_command(actions_sheet, actions_service)
            
        elif command.startswith("clear"):
            return self._handle_clear_command(command, actions_sheet)
            
        elif command.startswith("add"):
            return self._handle_add_command(command, actions_sheet)
            
        else:
            return False, f"Unknown command: {command}. Supported commands: clear all, clear id, clear group, add, render", None
    
    def _handle_render_command(self, actions_sheet: ActionsSheet, actions_service: ActionsService) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the 'render' command to render all actions to DMX canvas."""
        try:
            # Validate actions
            validation = actions_service.validate_actions(actions_sheet)
            valid_count = validation['valid_actions']
            total_count = validation['total_actions']
            
            # Render to canvas
            success = actions_service.render_actions_to_canvas(actions_sheet, clear_first=True)
            
            if success:
                # Get universe for broadcast
                from backend.dmx_controller import get_universe
                universe = get_universe()
                
                return True, f"Rendered {valid_count}/{total_count} actions to DMX canvas.", {
                    "universe": list(universe),
                    "message": "DMX Canvas updated by direct command"
                }
            else:
                return False, f"Failed to render actions to DMX canvas. {valid_count}/{total_count} actions valid.", None
                
        except Exception as e:
            return False, f"Error rendering actions: {e}", None
    
    def _handle_clear_command(self, command: str, actions_sheet: ActionsSheet) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the various 'clear' commands."""
        try:
            parts = command.split()
            
            if len(parts) < 2:
                return False, "Invalid clear command. Usage: clear all, clear id <action_id>, clear group <group_id>", None
                
            clear_type = parts[1].lower()
            
            if clear_type == "all":
                # Clear all actions
                initial_count = len(actions_sheet)
                actions_sheet.remove_all_actions()
                actions_sheet.save_actions()
                return True, f"Cleared all {initial_count} actions.", None
                
            elif clear_type == "id" and len(parts) >= 3:
                # Clear action by ID
                action_id = parts[2]
                
                # Find and remove the action with this ID
                found = False
                for i, action in enumerate(list(actions_sheet.actions)):
                    if action.action_id == action_id:
                        actions_sheet.remove_action(i)
                        found = True
                        break
                
                if found:
                    actions_sheet.save_actions()
                    return True, f"Removed action with ID {action_id}.", None
                else:
                    return False, f"No action found with ID {action_id}.", None
                    
            elif clear_type == "group" and len(parts) >= 3:
                # Clear actions by group ID
                group_id = parts[2]
                
                # Find and remove all actions with this group ID
                initial_count = len(actions_sheet)
                actions_to_remove = []
                
                for i, action in enumerate(list(actions_sheet.actions)):
                    if action.group_id == group_id:
                        actions_to_remove.append(i)
                
                # Remove in reverse order to avoid index shifting
                for i in sorted(actions_to_remove, reverse=True):
                    actions_sheet.remove_action(i)
                
                removed_count = initial_count - len(actions_sheet)
                if removed_count > 0:
                    actions_sheet.save_actions()
                    return True, f"Removed {removed_count} actions with group ID {group_id}.", None
                else:
                    return False, f"No actions found with group ID {group_id}.", None
            else:
                return False, "Invalid clear command. Usage: clear all, clear id <action_id>, clear group <group_id>", None
                
        except Exception as e:
            return False, f"Error clearing actions: {e}", None
    
    def _handle_add_command(self, command: str, actions_sheet: ActionsSheet) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the 'add' command to add a new action."""
        try:
            # Parse: add <action> to <fixture> at <start_time> duration <duration_time>
            add_match = re.match(
                r'add\s+(\w+)\s+to\s+(\w+)\s+at\s+([\d.]+)(?:s)?\s+duration\s+([\d.]+)(?:s)?',
                command
            )
            
            if not add_match:
                return False, "Invalid add command. Usage: add <action> to <fixture> at <start_time> duration <duration_time>", None
            
            action_name = add_match.group(1)
            fixture_id = add_match.group(2)
            start_time = float(add_match.group(3))
            duration = float(add_match.group(4))
            
            # Check if fixture exists
            if app_state.fixtures is None:
                return False, "Fixtures not initialized.", None
                
            if fixture_id not in app_state.fixtures.fixtures:
                return False, f"Fixture '{fixture_id}' not found.", None
            
            # Check if action is supported by fixture
            fixture = app_state.fixtures.fixtures[fixture_id]
            if action_name not in fixture.actions:
                supported_actions = ", ".join(fixture.actions)
                return False, f"Action '{action_name}' not supported by fixture '{fixture_id}'. Supported actions: {supported_actions}", None
            
            # Create action
            action = ActionModel(
                action=action_name,
                fixture_id=fixture_id,
                parameters={},  # Default empty parameters
                start_time=start_time,
                duration=duration
            )
            
            # Add to actions sheet
            actions_sheet.add_action(action)
            actions_sheet.save_actions()
            
            return True, f"Added {action_name} to {fixture_id} at {start_time}s for {duration}s.", None
            
        except Exception as e:
            return False, f"Error adding action: {e}", None
