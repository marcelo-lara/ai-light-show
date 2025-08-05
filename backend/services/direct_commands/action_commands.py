"""
Action-related command handlers (render, clear, add, direct actions).
"""
import re
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

from .base_command import BaseCommandHandler
from ...models.actions_sheet import ActionsSheet, ActionModel
from ..actions_service import ActionsService
from ..utils.time_conversion import string_to_time, beats_to_seconds


class RenderCommandHandler(BaseCommandHandler):
    """Handler for the 'render' command."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a render command."""
        return command.lower() == "render"
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the render command."""
        from ...models.app_state import app_state
        
        # Get current song and setup
        if not getattr(app_state, 'current_song_file', None):
            return False, "No song loaded. Please load a song first.", None
        
        song_file = getattr(app_state, 'current_song_file', None)
        if not song_file:
            return False, "No song loaded. Please load a song first.", None
            
        song_name = Path(song_file).stem
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        
        fixtures = getattr(app_state, 'fixtures', None)
        dmx_canvas = getattr(app_state, 'dmx_canvas', None)
        if fixtures is None or dmx_canvas is None:
            return False, "Fixtures or DMX canvas not initialized.", None
            
        actions_service = ActionsService(fixtures, dmx_canvas)
        
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


class ClearCommandHandler(BaseCommandHandler):
    """Handler for the 'clear' command variants."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a clear command."""
        return command.lower().startswith("clear")
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the clear command."""
        from ...models.app_state import app_state
        
        # Get current song and setup
        if not getattr(app_state, 'current_song_file', None):
            return False, "No song loaded. Please load a song first.", None
        
        song_file = getattr(app_state, 'current_song_file', None)
        if not song_file:
            return False, "No song loaded. Please load a song first.", None
            
        song_name = Path(song_file).stem
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        
        try:
            parts = command.split()
            
            if len(parts) < 2:
                return False, "Invalid clear command. Usage: 'clear all', 'clear all plans', 'clear all actions', 'clear id <action_id>', 'clear group <group_id>'", None
                
            clear_type = parts[1].lower()
            
            # Handle "clear all" - clears both lighting plans AND actions
            if clear_type == "all" and (len(parts) == 2 or (len(parts) > 2 and parts[2].lower() not in ["plans", "actions"])):
                # Check if confirmation flag is present
                confirmed = False
                for part in parts:
                    if part.lower() == "confirm" or part.lower() == "--confirm":
                        confirmed = True
                        break
                
                if not confirmed:
                    return False, "For safety, clearing all plans and actions requires confirmation. Please use '#clear all confirm' to proceed.", None
                
                # Clear both actions and lighting plans
                actions_count = len(actions_sheet)
                plans_count = len(app_state.current_song.light_plan) if app_state.current_song else 0
                
                # Clear actions
                actions_sheet.remove_all_actions()
                actions_sheet.save_actions()
                
                # Clear lighting plans
                if app_state.current_song:
                    app_state.current_song.clear_light_plan()
                    if hasattr(app_state.current_song, 'save'):
                        app_state.current_song.save()
                
                # Broadcast updates
                if websocket:
                    from ...services.utils.broadcast import broadcast_to_all
                    await broadcast_to_all({
                        "type": "lightPlanUpdate",
                        "light_plan": [],
                        "song_name": app_state.current_song.song_name if app_state.current_song else ""
                    })
                
                return True, f"Cleared all {actions_count} actions and {plans_count} lighting plans.", {
                    "actions_updated": True,
                    "plans_updated": True
                }
            
            # Handle "clear all plans" - clears only lighting plans
            elif clear_type == "all" and len(parts) >= 3 and parts[2].lower() == "plans":
                # Check if confirmation flag is present
                confirmed = False
                for part in parts:
                    if part.lower() == "confirm" or part.lower() == "--confirm":
                        confirmed = True
                        break
                
                if not confirmed:
                    return False, "For safety, clearing all plans requires confirmation. Please use '#clear all plans confirm' to proceed.", None
                
                # Clear only lighting plans
                plans_count = len(app_state.current_song.light_plan) if app_state.current_song else 0
                
                if app_state.current_song:
                    app_state.current_song.clear_light_plan()
                    if hasattr(app_state.current_song, 'save'):
                        app_state.current_song.save()
                
                # Broadcast plan update
                if websocket:
                    from ...services.utils.broadcast import broadcast_to_all
                    await broadcast_to_all({
                        "type": "lightPlanUpdate", 
                        "light_plan": [],
                        "song_name": app_state.current_song.song_name if app_state.current_song else ""
                    })
                
                return True, f"Cleared all {plans_count} lighting plans (actions preserved).", {
                    "plans_updated": True
                }
            
            # Handle "clear all actions" - clears only actions
            elif clear_type == "all" and len(parts) >= 3 and parts[2].lower() == "actions":
                # Check if confirmation flag is present
                confirmed = False
                for part in parts:
                    if part.lower() == "confirm" or part.lower() == "--confirm":
                        confirmed = True
                        break
                
                if not confirmed:
                    return False, "For safety, clearing all actions requires confirmation. Please use '#clear all actions confirm' to proceed.", None
                
                # Clear only actions
                actions_count = len(actions_sheet)
                actions_sheet.remove_all_actions()
                actions_sheet.save_actions()
                
                return True, f"Cleared all {actions_count} actions (lighting plans preserved).", {
                    "actions_updated": True
                }
                
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
                    return True, f"Removed action with ID {action_id}.", {
                        "actions_updated": True
                    }
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
                    return True, f"Removed {removed_count} actions with group ID {group_id}.", {
                        "actions_updated": True
                    }
                else:
                    return False, f"No actions found with group ID {group_id}.", None
            else:
                return False, "Invalid clear command. Usage: 'clear all', 'clear all plans', 'clear all actions', 'clear id <action_id>', 'clear group <group_id>'", None
                
        except Exception as e:
            return False, f"Error clearing: {e}", None


class AddCommandHandler(BaseCommandHandler):
    """Handler for the 'add' command."""
    
    def matches(self, command: str) -> bool:
        """Check if this is an add command."""
        return command.lower().startswith("add")
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the add command."""
        from ...models.app_state import app_state
        
        # Get current song and setup
        if not getattr(app_state, 'current_song_file', None):
            return False, "No song loaded. Please load a song first.", None
        
        song_file = getattr(app_state, 'current_song_file', None)
        if not song_file:
            return False, "No song loaded. Please load a song first.", None
            
        song_name = Path(song_file).stem
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        
        try:
            # Parse: add <action> to <fixture> at <start_time> duration <duration_time> or for <duration_time>
            add_match = re.match(
                r'add\s+(\w+)\s+to\s+(\w+)\s+at\s+([^ ]+)(?:\s+(?:duration|for)\s+([^ ]+))?',
                command
            )
            if not add_match:
                return False, "Invalid add command. Usage: add <action> to <fixture> at <start_time> duration <duration_time> or for <duration_time>", None
            action_name = add_match.group(1)
            fixture_id = add_match.group(2)
            start_time_str = add_match.group(3)
            duration_str = add_match.group(4) if add_match.group(4) else "1b"

            # Parse start_time and duration (support 1m23.45s, 2b, 12.5)
            bpm = getattr(app_state.current_song, "bpm", 120) if app_state.current_song else 120
            def parse_time(val):
                val = val.strip().lower()
                if val.endswith("b"):
                    try:
                        n_beats = float(val[:-1])
                        return beats_to_seconds(n_beats, bpm)
                    except Exception:
                        return 0.0
                return string_to_time(val)
            start_time = parse_time(start_time_str)
            duration = parse_time(duration_str)

            # Check if fixture exists
            if app_state.fixtures is None:
                return False, "Fixtures not initialized.", None
            if fixture_id not in app_state.fixtures.fixtures:
                return False, f"Fixture '{fixture_id}' not found.", None
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
            actions_sheet.add_action(action)
            actions_sheet.save_actions()
            return True, f"Added {action_name} to {fixture_id} at {start_time:.2f}s for {duration:.2f}s.", {
                "actions_updated": True
            }
        except Exception as e:
            return False, f"Error adding action: {e}", None


class DirectActionCommandHandler(BaseCommandHandler):
    """Handler for direct action commands like 'flash parcan_l at 135.78s'."""
    
    def matches(self, command: str) -> bool:
        """This handler matches any command that other handlers don't match."""
        return True  # This is the fallback handler
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle direct action commands."""
        from ...models.app_state import app_state
        
        # Get current song and setup
        if not getattr(app_state, 'current_song_file', None):
            return False, "No song loaded. Please load a song first.", None
        
        song_file = getattr(app_state, 'current_song_file', None)
        if not song_file:
            return False, "No song loaded. Please load a song first.", None
            
        song_name = Path(song_file).stem
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        
        fixtures = getattr(app_state, 'fixtures', None)
        dmx_canvas = getattr(app_state, 'dmx_canvas', None)
        if fixtures is None or dmx_canvas is None:
            return False, "Fixtures or DMX canvas not initialized.", None
            
        actions_service = ActionsService(fixtures, dmx_canvas)
        
        try:
            # Import here to avoid circular imports
            from ..dmx.actions_parser_service import ActionsParserService
            
            # Create actions parser
            if app_state.fixtures is None:
                return False, "Fixtures not initialized.", None
                
            parser = ActionsParserService(app_state.fixtures, debug=False)
            
            # Try to parse the command
            actions = parser.parse_command(command)
            
            if not actions:
                return False, f"Could not parse action command: {command}. Try using #add format instead.", None
            
            # Add all parsed actions to the actions sheet
            added_count = 0
            for action in actions:
                actions_sheet.add_action(action)
                added_count += 1
            
            # Save actions
            actions_sheet.save_actions()
            
            # Optionally render immediately
            render_success = actions_service.render_actions_to_canvas(actions_sheet, clear_first=False)
            
            # Create response message
            action_descriptions = [f"{action.action} on {action.fixture_id} at {action.start_time:.2f}s" for action in actions]
            action_list = ", ".join(action_descriptions)
            
            if render_success:
                # Get universe for broadcast
                from backend.dmx_controller import get_universe
                universe = get_universe()
                
                return True, f"Added and rendered {added_count} action(s): {action_list}", {
                    "universe": list(universe),
                    "message": "DMX Canvas updated by direct action command",
                    "actions_updated": True
                }
            else:
                return True, f"Added {added_count} action(s): {action_list} (render to see effect)", {
                    "actions_updated": True
                }
                
        except Exception as e:
            return False, f"Error processing direct action command: {e}", None
