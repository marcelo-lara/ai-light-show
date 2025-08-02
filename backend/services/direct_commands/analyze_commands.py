"""
Analyze command handlers for song analysis and context analysis.
"""
from typing import Dict, Any, Tuple, Optional
from pathlib import Path

from .base_command import BaseCommandHandler


class AnalyzeCommandHandler(BaseCommandHandler):
    """Handler for the 'analyze' command."""
    
    def matches(self, command: str) -> bool:
        """Check if this is an analyze command."""
        return command.lower() == "analyze"
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the analyze command."""
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


class AnalyzeContextCommandHandler(BaseCommandHandler):
    """Handler for the 'analyze context' command."""
    
    def matches(self, command: str) -> bool:
        """Check if this is an analyze context command."""
        return command.lower().startswith("analyze context")
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the analyze context command."""
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
                from ..agents import SongContextAgent
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


class AnalyzeBeatsCommandHandler(BaseCommandHandler):
    """Handler for the 'analyze beats' command to get beat times for specific time ranges."""
    
    def matches(self, command: str) -> bool:
        """Check if this is an analyze beats command."""
        return command.lower().startswith("analyze beats")
    
    async def handle(self, command: str, websocket=None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Handle the analyze beats command."""
        import re
        
        # Parse command: "analyze beats <start_time> <end_time>"
        match = re.match(r"analyze\s+beats\s+([\d.]+)\s+([\d.]+)", command.lower())
        if not match:
            return False, "Invalid format. Use: #analyze beats <start_time> <end_time>", None
        
        start_time = float(match.group(1))
        end_time = float(match.group(2))
        
        if start_time >= end_time:
            return False, "Start time must be less than end time", None
        
        try:
            from ..song_analysis_client import SongAnalysisClient
            from ...models.app_state import app_state
            
            # Get current song
            current_song = getattr(app_state, 'current_song', None)
            if not current_song:
                return False, "No song loaded for beat analysis", None
            
            song_name = Path(current_song.mp3_path).stem if getattr(current_song, 'mp3_path', None) else None
            if not song_name:
                return False, "No song file path available", None
            
            # Request beats from song analysis service
            async with SongAnalysisClient() as client:
                health = await client.health_check()
                if health.get("status") != "healthy":
                    return False, f"Song analysis service is not healthy: {health.get('error', 'Unknown error')}", None
                
                # Use the analyze endpoint to get beats for the specific time range
                result = await client.analyze_beats_rms_flux(
                    song_name=song_name, 
                    start_time=start_time, 
                    end_time=end_time,
                    force=False  # Use cache if available
                )
                
                if result.get("status") == "ok":
                    beats = result.get("beats", [])
                    
                    # Filter beats to the requested time range (double-check)
                    filtered_beats = [beat for beat in beats if start_time <= beat <= end_time]
                    
                    if websocket:
                        await websocket.send_json({
                            "type": "analyzeBeatsResult",
                            "status": "ok",
                            "start_time": start_time,
                            "end_time": end_time,
                            "beats": filtered_beats,
                            "beat_count": len(filtered_beats)
                        })
                    
                    beat_times_str = ", ".join([f"{beat:.3f}s" for beat in filtered_beats[:10]])  # Show first 10 beats
                    if len(filtered_beats) > 10:
                        beat_times_str += f" ... ({len(filtered_beats)} total beats)"
                    
                    return True, f"Found {len(filtered_beats)} beats between {start_time}s and {end_time}s: {beat_times_str}", {
                        "beats": filtered_beats,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                else:
                    error_msg = result.get("message", "Unknown error")
                    return False, f"Beat analysis failed: {error_msg}", None
                    
        except Exception as e:
            error_message = f"Error analyzing beats: {str(e)}"
            if websocket:
                await websocket.send_json({
                    "type": "analyzeBeatsResult",
                    "status": "error",
                    "message": error_message
                })
            return False, error_message, None
