"""
Direct Commands Parser

This service parses direct action commands sent by the user through ChatAssistant.
Commands start with #action and bypass the LLM processing.
"""
import re
from typing import Dict, Any, Tuple, List, Optional
from pathlib import Path
from datetime import datetime

from ...models.app_state import app_state
from ...models.actions_sheet import ActionsSheet, ActionModel
from ..actions_service import ActionsService
from ..utils.time_conversion import string_to_time, beats_to_seconds
from ..agents import SongContextAgent  # Import from unified agents


class DirectCommandsParser:
    """Parser for direct action commands from ChatAssistant."""
    
    def __init__(self):
        """Initialize the direct commands parser."""
        pass
    
    async def parse_command(self, command_text: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Parse a direct command and execute it. Async to allow calling async handlers.
        
        Args:
            command_text (str): The command text from the user (starts with #action)
            websocket: WebSocket, required for #analyze
            
        Returns:
            Tuple[bool, str, Optional[Dict[str, Any]]]: 
                - Success flag
                - Message to return to the user
                - Additional data (if any)
        """
        # Accept both #action and # as prefix
        command = command_text.lstrip("#").strip()
        command = command.replace("action", "", 1).strip() if command.lower().startswith("action") else command

        # #help command
        if command.lower() == "help":
            help_text = (
                "Direct Commands:\n"
                "- #help - Show this help message\n"
                "- #clear all actions - Clear all actions from the current song\n"
                "- #clear action <action_id> - Clear a specific action by ID\n"
                "- #clear group <group_id> - Clear all actions with a specific group ID\n"
                "- #add <action> to <fixture> at <start_time> duration <duration_time> OR for <duration_time> - Add a new action. Duration is optional, default is 1 beat.\n"
                "- #render - Render all actions to the DMX canvas\n"
                "- #analyze - Analyze the current song using the analysis service\n"
                "- #analyze context - Generate lighting context for the current song using AI (runs in background)\n"
                "- #analyze context reset - Clear existing context analysis and start fresh\n"
                "- #tasks - Show status of background tasks\n"
                "\nAccepted time formats: 1m23.45s, 2b (beats), 12.5 (seconds)\n"
                "\nNote: Background tasks continue running even if you close the browser.\n"
            )
            return True, help_text, None

        # #tasks command
        if command.lower() == "tasks":
            from ...models.app_state import app_state
            
            if not app_state.background_tasks:
                return True, "No background tasks found.", None
            
            task_list = []
            task_list.append("Background Tasks:")
            task_list.append("-" * 50)
            
            for task_id, task_state in app_state.background_tasks.items():
                status_emoji = "🔄" if task_state.status == "running" else "✅" if task_state.status == "completed" else "❌"
                elapsed = (datetime.now() - task_state.started_at).total_seconds()
                
                task_list.append(f"{status_emoji} {task_id}")
                task_list.append(f"   Song: {task_state.song_name}")
                task_list.append(f"   Operation: {task_state.operation}")
                task_list.append(f"   Status: {task_state.status}")
                task_list.append(f"   Progress: {task_state.progress}% ({task_state.current}/{task_state.total})")
                task_list.append(f"   Started: {elapsed:.1f}s ago")
                if task_state.message:
                    task_list.append(f"   Message: {task_state.message}")
                if task_state.error:
                    task_list.append(f"   Error: {task_state.error}")
                task_list.append("")
            
            return True, "\n".join(task_list), None

        # #analyze context command
        if command.lower().startswith("analyze context"):
            if websocket is not None:
                try:
                    # Check if a song is loaded
                    from ...models.app_state import app_state
                    current_song = getattr(app_state, 'current_song', None)
                    if not current_song:
                        await websocket.send_json({
                            "type": "analyzeContextResult",
                            "status": "error",
                            "message": "No song loaded for context analysis"
                        })
                        return False, "No song loaded for context analysis.", None
                    
                    # Check for reset flag
                    is_reset = "reset" in command.lower()
                    
                    if is_reset:
                        # Clear existing context file
                        from pathlib import Path as PathLib
                        context_file_path = PathLib(current_song.context_file)
                        if context_file_path.exists():
                            try:
                                context_file_path.unlink()
                                await websocket.send_json({
                                    "type": "analyzeContextResult", 
                                    "status": "info",
                                    "message": "Cleared existing context analysis. Starting fresh..."
                                })
                            except Exception as e:
                                await websocket.send_json({
                                    "type": "analyzeContextResult",
                                    "status": "error", 
                                    "message": f"Failed to clear context file: {str(e)}"
                                })
                                return False, f"Failed to clear context file: {str(e)}", None
                    
                    # Check if there's already a context analysis in progress or completed
                    from pathlib import Path as PathLib
                    context_file_path = PathLib(current_song.context_file)
                    resume_info = ""
                    
                    if not is_reset and context_file_path.exists():
                        try:
                            import json
                            with open(context_file_path, 'r') as f:
                                existing_data = json.load(f)
                            
                            if isinstance(existing_data, dict) and 'analysis_progress' in existing_data:
                                progress = existing_data['analysis_progress']
                                if progress.get('progress_percent', 0) < 100:
                                    completed = progress.get('completed_chunks', 0)
                                    total = progress.get('total_chunks', 0)
                                    resume_info = f" Will resume from chunk {completed + 1}/{total}."
                                else:
                                    resume_info = " Previous analysis found, will refresh with new analysis."
                        except Exception:
                            pass
                    
                    # Import and use the SongContextAgent
                    agent = SongContextAgent()
                    
                    # Notify the client that analysis is starting
                    await websocket.send_json({
                        "type": "analyzeContextResult",
                        "status": "processing",
                        "message": f"Generating lighting context, please wait...{resume_info}"
                    })
                    
                    # Call the analyze_song_context method in the background
                    try:
                        import asyncio
                        import uuid
                        
                        # Generate unique task ID
                        task_id = f"analyze_context_{current_song.song_name}_{uuid.uuid4().hex[:8]}"
                        
                        # Create a background task
                        async def run_analysis():
                            try:
                                timeline = await agent.analyze_song_context(websocket=websocket, task_id=task_id)
                                
                                # Send final result to all connected clients
                                app_state.broadcast_to_clients({
                                    "type": "analyzeContextResult",
                                    "status": "ok",
                                    "task_id": task_id,
                                    "message": f"Successfully generated lighting context with {len(timeline)} actions",
                                    "timeline": timeline
                                })
                            except Exception as e:
                                error_message = f"Error generating lighting context: {str(e)}"
                                app_state.broadcast_to_clients({
                                    "type": "analyzeContextResult",
                                    "status": "error",
                                    "task_id": task_id,
                                    "message": error_message
                                })
                        
                        # Start the background task
                        task = asyncio.create_task(run_analysis())
                        
                        # Store task reference in app_state
                        if task_id in app_state.background_tasks:
                            app_state.background_tasks[task_id].task = task
                        
                        # Return immediately to user
                        action_word = "restarted" if is_reset else "started"
                        return True, f"Context analysis {action_word} in background (Task ID: {task_id}). Process will continue even if you close the browser.{resume_info}", None
                    except Exception as e:
                        error_message = f"Error generating lighting context: {str(e)}"
                        await websocket.send_json({
                            "type": "analyzeContextResult",
                            "status": "error",
                            "message": error_message
                        })
                        return False, error_message, None
                    
                except Exception as e:
                    error_message = f"Error in analyze context command: {str(e)}"
                    if websocket:
                        await websocket.send_json({
                            "type": "analyzeContextResult",
                            "status": "error",
                            "message": error_message
                        })
                    return False, error_message, None
            return False, "WebSocket connection required for analyze context command", None

        # #analyze command
        if command.lower() == "analyze":
            if websocket is not None:
                try:
                    from ..song_analysis_client import SongAnalysisClient
                    from ...models.app_state import app_state
                    current_song = getattr(app_state, 'current_song', None)
                    song_name = Path(current_song.mp3_path).stem if current_song and getattr(current_song, 'mp3_path', None) else None
                    if not song_name or not current_song:
                        await websocket.send_json({
                            "type": "analyzeResult",
                            "status": "error",
                            "message": "No song loaded for analysis"
                        })
                        return False, "No song loaded for analysis.", None
                    async with SongAnalysisClient() as client:
                        health = await client.health_check()
                        if health.get("status") != "healthy":
                            await websocket.send_json({
                                "type": "analyzeResult",
                                "status": "error",
                                "message": f"Song analysis service is not healthy: {health.get('error', 'Unknown error')}"
                            })
                            return False, "Song analysis service is not healthy.", None
                        result = await client.analyze_song(song_name=song_name, reset_file=True, debug=False)
                        if result.get("status") == "success":
                            metadata = result.get("metadata", {})
                            # Update app_state.current_song with new metadata
                            if current_song:
                                current_song.bpm = metadata.get("bpm", getattr(current_song, "bpm", None))
                                current_song.duration = metadata.get("duration", getattr(current_song, "duration", None))
                                current_song.beats = metadata.get("beats", [])
                                current_song.patterns = metadata.get("patterns", [])
                                current_song.chords = metadata.get("chords", [])
                                current_song.drums = metadata.get("drums", [])
                                current_song.arrangement = metadata.get("arrangement", [])
                                current_song.key_moments = metadata.get("key_moments", [])
                                if hasattr(current_song, "save"):
                                    current_song.save()
                            await websocket.send_json({
                                "type": "analyzeResult",
                                "status": "ok",
                                "metadata": metadata
                            })
                            return True, "Song analysis completed successfully.", None
                        else:
                            await websocket.send_json({
                                "type": "analyzeResult",
                                "status": "error",
                                "message": result.get("message", "Analysis failed")
                            })
                            return False, result.get("message", "Analysis failed"), None
                except Exception as e:
                    await websocket.send_json({
                        "type": "analyzeResult",
                        "status": "error",
                        "message": f"Analysis failed: {str(e)}"
                    })
                    return False, f"Analysis failed: {str(e)}", None
            else:
                return False, "WebSocket required for #analyze command.", None

        # Get current song
        from ...models.app_state import app_state
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
        # Handle different command types
        if command == "render":
            return self._handle_render_command(actions_sheet, actions_service)
        elif command.startswith("clear"):
            return self._handle_clear_command(command, actions_sheet)
        elif command.startswith("add"):
            return self._handle_add_command(command, actions_sheet)
        else:
            return False, f"Unknown command: {command}. Supported commands: clear all, clear id, clear group, add, render, analyze", None
    
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
            return True, f"Added {action_name} to {fixture_id} at {start_time:.2f}s for {duration:.2f}s.", None
        except Exception as e:
            return False, f"Error adding action: {e}", None
