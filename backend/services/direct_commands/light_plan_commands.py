"""
Light plan command handlers for managing LightPlanItems in song metadata.
"""
import re
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

from .base_command import BaseCommandHandler
from ..utils.time_conversion import string_to_time, beats_to_seconds


class CreateLightPlanCommandHandler(BaseCommandHandler):
    """Handler for creating light plan items."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a create light plan command."""
        return command.lower().startswith("create plan") or command.lower().startswith("plan create")
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the create light plan command."""
        from ...models.app_state import app_state
        
        # Check if a valid song is loaded (not just the placeholder)
        if not app_state.current_song or not hasattr(app_state.current_song, 'song_name') or app_state.current_song.song_name == '_not_loaded_':
            return False, "Error: You can't create light plan items without a song loaded. Please load a song first.", None
        
        try:
            # Parse command formats:
            # create plan <name> at <start_time> [to <end_time>] [description <description>]
            # plan create <name> at <start_time> [to <end_time>] [description <description>]
            
            # Remove the command prefix
            if command.lower().startswith("create plan"):
                params = command[11:].strip()
            elif command.lower().startswith("plan create"):
                params = command[11:].strip()
            else:
                return False, "Invalid create plan command format.", None
            
            # Parse the parameters
            # Pattern: <name> at <start_time> [to <end_time>] [description <description>]
            match = re.match(
                r'^(.+?)\s+at\s+([^\s]+)(?:\s+to\s+([^\s]+))?(?:\s+description\s+(.+))?$',
                params,
                re.IGNORECASE
            )
            
            if not match:
                return False, "Invalid format. Use: create plan <name> at <start_time> [to <end_time>] [description <description>]", None
            
            plan_name = match.group(1).strip()
            start_time_str = match.group(2).strip()
            end_time_str = match.group(3).strip() if match.group(3) else None
            description = match.group(4).strip() if match.group(4) else None
            
            # Parse times
            bpm = getattr(app_state.current_song, "bpm", 120)
            
            def parse_time(time_str):
                time_str = time_str.strip().lower()
                if time_str.endswith("b"):
                    try:
                        n_beats = float(time_str[:-1])
                        return beats_to_seconds(n_beats, bpm)
                    except Exception:
                        return 0.0
                return string_to_time(time_str)
            
            start_time = parse_time(start_time_str)
            end_time = parse_time(end_time_str) if end_time_str else None
            
            # Validate times
            if start_time < 0:
                return False, "Start time cannot be negative.", None
            
            if end_time is not None and end_time <= start_time:
                return False, "End time must be after start time.", None
            
            # Import LightPlanItem
            from shared.models.light_plan_item import LightPlanItem
            
            # Generate unique ID
            existing_ids = [plan.id for plan in app_state.current_song.light_plan]
            new_id = max(existing_ids) + 1 if existing_ids else 1
            
            # Add light plan item using the SongMetadata method
            app_state.current_song.add_light_plan_item(
                id=new_id,
                start=start_time,
                end=end_time,
                name=plan_name,
                description=description
            )
            
            # Save the song metadata
            if hasattr(app_state.current_song, 'save'):
                app_state.current_song.save()
            
            # Create response message
            time_range = f"{start_time:.2f}s"
            if end_time is not None:
                time_range += f" to {end_time:.2f}s"
            
            desc_text = f" ({description})" if description else ""
            
            # Create light plan item for response
            from shared.models.light_plan_item import LightPlanItem
            created_plan = LightPlanItem(
                id=new_id,
                start=start_time,
                end=end_time,
                name=plan_name,
                description=description
            )
            
            return True, f"Created light plan '{plan_name}' (ID: {new_id}) at {time_range}{desc_text}", {
                "light_plan": created_plan.to_dict()
            }
            
        except Exception as e:
            return False, f"Error creating light plan: {e}", None


class DeleteLightPlanCommandHandler(BaseCommandHandler):
    """Handler for deleting light plan items."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a delete light plan command."""
        return (command.lower().startswith("delete plan") or 
                command.lower().startswith("plan delete") or
                command.lower().startswith("remove plan") or
                command.lower().startswith("plan remove"))
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the delete light plan command."""
        from ...models.app_state import app_state
        
        # Check if a valid song is loaded (not just the placeholder)
        if not app_state.current_song or not hasattr(app_state.current_song, 'song_name') or app_state.current_song.song_name == '_not_loaded_':
            return False, "Error: You can't delete light plan items without a song loaded. Please load a song first.", None
        
        try:
            # Parse command formats:
            # delete plan <id>
            # delete plan <name>
            # plan delete <id>
            # remove plan <id>
            
            # Extract the identifier
            parts = command.split()
            if len(parts) < 3:
                return False, "Invalid format. Use: delete plan <id> or delete plan <name>", None
            
            identifier = " ".join(parts[2:])  # Join remaining parts as name might have spaces
            
            # Get existing light plans
            light_plans = app_state.current_song.light_plan
            if not light_plans:
                return False, "No light plans found in the current song.", None
            
            # Find the plan to delete
            plan_to_delete = None
            
            # Try to find by ID first
            try:
                plan_id = int(identifier)
                for plan in light_plans:
                    if plan.id == plan_id:
                        plan_to_delete = plan
                        break
            except ValueError:
                # Not a number, try to find by name
                for plan in light_plans:
                    if plan.name.lower() == identifier.lower():
                        plan_to_delete = plan
                        break
            
            if plan_to_delete is None:
                return False, f"Light plan '{identifier}' not found.", None
            
            # Remove the plan using SongMetadata method
            success = app_state.current_song.remove_light_plan_item(plan_to_delete.id)
            
            if not success:
                return False, f"Failed to remove light plan '{identifier}'.", None
            
            # Save the song metadata
            if hasattr(app_state.current_song, 'save'):
                app_state.current_song.save()
            
            return True, f"Deleted light plan '{plan_to_delete.name}' (ID: {plan_to_delete.id})", None
            
        except Exception as e:
            return False, f"Error deleting light plan: {e}", None


class ResetLightPlansCommandHandler(BaseCommandHandler):
    """Handler for resetting (deleting all) light plan items."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a reset light plans command."""
        return (command.lower().startswith("reset plans") or 
                command.lower().startswith("plans reset") or
                command.lower().startswith("clear plans") or
                command.lower().startswith("plans clear"))
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the reset light plans command."""
        from ...models.app_state import app_state
        
        # Check if a valid song is loaded (not just the placeholder)
        if not app_state.current_song or not hasattr(app_state.current_song, 'song_name') or app_state.current_song.song_name == '_not_loaded_':
            return False, "Error: You can't reset light plan items without a song loaded. Please load a song first.", None
        
        try:
            # Get existing light plans
            light_plans = app_state.current_song.light_plan
            plan_count = len(light_plans)
            
            if plan_count == 0:
                return True, "No light plans to reset (already empty).", None
            
            # Clear all light plans using SongMetadata method
            app_state.current_song.clear_light_plan()
            
            # Save the song metadata
            if hasattr(app_state.current_song, 'save'):
                app_state.current_song.save()
            
            return True, f"Reset {plan_count} light plan(s) from the current song.", None
            
        except Exception as e:
            return False, f"Error resetting light plans: {e}", None


class ListLightPlansCommandHandler(BaseCommandHandler):
    """Handler for listing light plan items."""
    
    def matches(self, command: str) -> bool:
        """Check if this is a list light plans command."""
        return (command.lower().startswith("list plans") or 
                command.lower().startswith("plans list") or
                command.lower().startswith("show plans") or
                command.lower().startswith("plans show") or
                command.lower() == "plans")
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the list light plans command."""
        from ...models.app_state import app_state
        
        # Check if a valid song is loaded (not just the placeholder)
        if not app_state.current_song or not hasattr(app_state.current_song, 'song_name') or app_state.current_song.song_name == '_not_loaded_':
            return False, "Error: You can't list light plan items without a song loaded. Please load a song first.", None
        
        try:
            # Get existing light plans
            light_plans = app_state.current_song.light_plan
            
            if not light_plans:
                return True, "No light plans found in the current song.", None
            
            # Sort plans by start time
            sorted_plans = sorted(light_plans, key=lambda p: p.start)
            
            # Create formatted list
            plan_list = []
            plan_list.append(f"Light Plans for '{app_state.current_song.song_name}':")
            plan_list.append("-" * 50)
            
            for plan in sorted_plans:
                time_range = f"{plan.start:.2f}s"
                if plan.end is not None:
                    duration = plan.end - plan.start
                    time_range += f" to {plan.end:.2f}s ({duration:.2f}s)"
                else:
                    time_range += " (no end time)"
                
                plan_list.append(f"[{plan.id}] {plan.name}")
                plan_list.append(f"    Time: {time_range}")
                if plan.description:
                    plan_list.append(f"    Description: {plan.description}")
                plan_list.append("")
            
            return True, "\n".join(plan_list), {
                "light_plans": [plan.to_dict() for plan in sorted_plans]
            }
            
        except Exception as e:
            return False, f"Error listing light plans: {e}", None
