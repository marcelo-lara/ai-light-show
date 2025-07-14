"""WebSocket service for real-time communication."""

import asyncio
import time
from typing import Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from ..models.app_state import app_state
from ..fixture_utils import load_fixtures_config
from ..models.song_metadata import SongMetadata, Section
from ..config import SONGS_DIR
from ..services.dmx_canvas import DmxCanvas

class WebSocketManager:
    """Manages WebSocket connections and message handling."""
    
    def __init__(self):
        # Debouncing for DMX updates
        self._dmx_update_task = None
        self._dmx_pending_updates = {}
        self._dmx_debounce_delay = 0.5  # 500ms
        
        self.message_handlers = {
            "sync": self._handle_sync,
            "loadSong": self._handle_load_song,
            "previewDmx": self._handle_preview_dmx,
            "saveArrangement": self._handle_save_arrangement,
            "saveKeyMoments": self._handle_save_key_moments,
            "analyzeSong": self._handle_analyze_song,
            "reloadFixtures": self._handle_reload_fixtures,
            "setDmx": self._handle_set_dmx,
            "userPrompt": self._handle_user_prompt,
            "blackout": self._handle_blackout,
        }

    async def _handle_user_prompt(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle userPrompt with streaming and action proposals/confirmation flow."""
        from ..services.ollama import query_ollama_mistral_streaming, extract_action_proposals, execute_confirmed_action
        
        prompt = message.get("text", "") or message.get("prompt", "")
        if not prompt:
            await websocket.send_json({"type": "chatResponse", "response": "No prompt provided."})
            return
        
        try:
            session_id = str(id(websocket))
            
            # Check if this is a confirmation message for pending actions
            # Store pending actions in a class attribute keyed by websocket ID
            if not hasattr(self, '_pending_actions_store'):
                self._pending_actions_store = {}
            
            pending_actions = self._pending_actions_store.get(session_id)
            if pending_actions:
                # Parse confirmation response
                prompt_lower = prompt.lower().strip()
                is_confirmation = any(word in prompt_lower for word in ['yes', 'confirm', 'do it', 'execute', 'go ahead'])
                is_rejection = any(word in prompt_lower for word in ['no', 'cancel', 'stop', 'nevermind', 'don\'t'])
                
                if is_confirmation:
                    # Execute all pending actions
                    results = []
                    any_success = False
                    for action in pending_actions:
                        success, message_result = execute_confirmed_action(action['id'], pending_actions)
                        results.append(f"✓ {message_result}" if success else f"✗ {message_result}")
                        if success:
                            any_success = True
                        print(f"🎭 ACTION EXECUTED: {action['command']} -> {'SUCCESS' if success else 'FAILED'}: {message_result}")
                    
                    response_text = "Actions executed:\n" + "\n".join(results)
                    await websocket.send_json({
                        "type": "chatResponse", 
                        "response": response_text,
                        "action_proposals": []
                    })
                    
                    # Broadcast updates to all clients if any action succeeded
                    # TODO: Implement DMX Canvas update broadcast
                    # This should broadcast the updated canvas state to all clients
                    if any_success:
                        await broadcast_to_all({
                            "type": "dmxCanvasUpdated",
                            "message": "DMX Canvas updated by AI actions"
                        })
                    
                    # Clear pending actions
                    del self._pending_actions_store[session_id]
                    return
                    
                elif is_rejection:
                    await websocket.send_json({
                        "type": "chatResponse", 
                        "response": "Actions cancelled.",
                        "action_proposals": []
                    })
                    
                    # Clear pending actions
                    del self._pending_actions_store[session_id]
                    return
            
            # Start streaming response
            await websocket.send_json({"type": "chatResponseStart"})
            
            # Collect full response for action processing
            full_ai_response = ""
            
            # Send chunk callback for streaming
            async def send_chunk(chunk):
                nonlocal full_ai_response
                full_ai_response += chunk
                await websocket.send_json({
                    "type": "chatResponseChunk", 
                    "chunk": chunk
                })
            
            # Stream the AI response
            try:
                await query_ollama_mistral_streaming(prompt, session_id, callback=send_chunk)
                # Process action proposals from the full response only if AI succeeded
                cleaned_response, action_proposals = extract_action_proposals(full_ai_response, session_id)
            except (ConnectionError, TimeoutError, ValueError, RuntimeError) as ai_error:
                # Handle AI service errors gracefully
                print(f"🤖 AI Service Error: {ai_error}")
                
                # Send a helpful error message as a chunk
                error_chunk = f"\n\nSorry, I'm having trouble connecting to the AI service. {str(ai_error)}\n\nPlease check that Ollama is running and the 'mistral' model is installed."
                await send_chunk(error_chunk)
                
                # Don't process action proposals if AI failed
                action_proposals = []
            
            # End streaming
            await websocket.send_json({"type": "chatResponseEnd"})
            
            # If there are action proposals, store them and ask for confirmation
            if action_proposals:
                self._pending_actions_store[session_id] = action_proposals
                
                # Create confirmation prompt
                action_descriptions = []
                for action in action_proposals:
                    if action.get('can_execute', False):
                        action_descriptions.append(f"• {action.get('description', action.get('command', 'Unknown action'))}")
                
                if action_descriptions:
                    confirmation_text = f"\n\n**I want to make these lighting changes:**\n" + "\n".join(action_descriptions)
                    confirmation_text += f"\n\nDo you want me to execute these changes? Please reply 'yes' to confirm or 'no' to cancel."
                    
                    # Send the confirmation prompt as a follow-up message
                    await websocket.send_json({
                        "type": "chatResponse", 
                        "response": confirmation_text,
                        "action_proposals": action_proposals
                    })
                    
                    print(f"🎭 ACTION PROPOSALS: {len(action_proposals)} actions proposed for session {session_id}")
                    for action in action_proposals:
                        print(f"   - {action.get('description', action.get('command', 'Unknown'))}")
            
        except Exception as e:
            print(f"❌ Error in _handle_user_prompt: {e}")
            
            # Provide user-friendly error messages
            error_message = "Sorry, I'm having trouble connecting to the AI service right now. Please check if the Ollama service is running and try again."
            
            # Check for specific error types
            if "Connection" in str(e) or "connect" in str(e).lower():
                error_message = "Can't connect to the AI service. Please make sure Ollama is running on http://backend-llm:11434"
            elif "timeout" in str(e).lower():
                error_message = "The AI service is taking too long to respond. Please try again in a moment."
            elif "model" in str(e).lower():
                error_message = "The 'mistral' model is not available. Please check that it's installed in Ollama."
            
            # Send streaming end if we started streaming
            try:
                await websocket.send_json({"type": "chatResponseEnd"})
            except:
                pass
            
            # Send the error as a chat response
            await websocket.send_json({
                "type": "chatResponse", 
                "response": error_message
            })
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        app_state.add_client(websocket)
        print(f"🧠 Client connected: {websocket.client}")
        
        # Send initial setup data
        await websocket.send_json({
            "type": "setup",
            "songs": app_state.get_songs_list(),
            "fixtures": app_state.fixture_config,
            "presets": app_state.fixture_presets
        })
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection."""
        app_state.remove_client(websocket)
        
        # Clean up pending actions for this websocket
        session_id = str(id(websocket))
        if hasattr(self, '_pending_actions_store') and session_id in self._pending_actions_store:
            del self._pending_actions_store[session_id]
        
        print(f"👋 Client disconnected: {websocket.client}")
    
    async def handle_message(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Route message to appropriate handler."""
        msg_type = message.get("type")
        
        if msg_type in self.message_handlers:
            try:
                await self.message_handlers[msg_type](websocket, message)
            except Exception as e:
                print(f"❌ Error handling {msg_type}: {e}")
                await websocket.send_json({
                    "type": "error", 
                    "message": f"Error handling {msg_type}: {str(e)}"
                })
        else:
            print(f"❓ Unknown message type: {msg_type}")
            print(f"  Message content: {message}")            
            await websocket.send_json({
                "type": "error", 
                "message": "Unknown message type"
            })
    
    async def _handle_sync(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle playback synchronization."""
        from .dmx_player import dmx_player
        
        # Use the sync_playback method for smart synchronization
        is_playing = message.get("isPlaying", dmx_player.is_playing())
        current_time = message.get("currentTime", dmx_player.get_current_time())
        
        dmx_player.sync_playback(is_playing, current_time)

        await websocket.send_json({
            "type": "syncAck",
            "isPlaying": dmx_player.playback_state.is_playing,
            "currentTime": dmx_player.playback_state.get_current_time()
        })

    async def _handle_blackout(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle blackout request."""
        from ..dmx_controller import send_blackout
        send_blackout()        

    async def _handle_load_song(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle song loading."""
        song_file = message["file"]
        print(f"🎶 Loading song: {song_file}")
        
        app_state.current_song_file = song_file
        app_state.current_song = SongMetadata(song_file, songs_folder=str(SONGS_DIR))

        # Re-initialize the DmxCanvas with the new song duration
        song_duration = app_state.current_song.duration
        if song_duration > 0:
            print(f"🎛️ Re-initializing DMX Canvas with duration: {song_duration:.2f}s")
            app_state.dmx_canvas = DmxCanvas(fps=44, duration=song_duration)
        else:
            # TODO: Handle songs without duration metadata
            # Consider using a default duration or audio file length detection
            print("⚠️ Song duration not available, using default canvas duration")
            app_state.dmx_canvas = DmxCanvas(fps=44, duration=300.0)  # 5 minute default

        await websocket.send_json({
            "type": "songLoaded",
            "metadata": app_state.current_song.to_dict(),
            "message": f"Song loaded - DMX Canvas initialized with {song_duration:.2f}s duration"
        })
    
    
    async def _handle_preview_dmx(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """DEPRECATED: DMX preview using old cue system - functionality removed."""
        # DEPRECATED: Cue preview system removed
        print(f"� DEPRECATED: Preview cue functionality removed")
        
        await websocket.send_json({
            "type": "error",
            "message": "DEPRECATED: Cue preview functionality has been removed"
        })
    
    async def _handle_save_arrangement(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle saving song arrangement."""
        arrangement = message["arrangement"]
        if app_state.current_song is not None:
            app_state.current_song.arrangement = {k: Section(**v) for k, v in arrangement.items()}
            app_state.current_song.save()
        else:
            print("No song object loaded; cannot save arrangement.")
    
    async def _handle_save_key_moments(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle saving song key moments."""
        key_moments = message["key_moments"]
        if app_state.current_song is not None:
            app_state.current_song.key_moments = key_moments
            app_state.current_song.save()
            print(f"✅ Saved {len(key_moments)} key moments for {app_state.current_song.song_name}")
        else:
            print("No song object loaded; cannot save key moments.")

    
    async def _handle_analyze_song(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle song analysis."""
        from .song_analyze import song_analyze
        
        if not app_state.current_song:
            print("❌ No song loaded for analysis")
            return

        app_state.current_song = song_analyze(app_state.current_song)
        app_state.current_song.save()

        await websocket.send_json({
            "type": "analyzeResult",
            "status": "ok",
            "metadata": app_state.current_song.to_dict()
        })

        # DEPRECATED: Test cue generation removed
        create_test = message.get("renderTestCues", False)
        if create_test:
            print("� DEPRECATED: Test cue generation has been removed")
            await websocket.send_json({
                "type": "error",
                "message": "DEPRECATED: Test cue generation functionality has been removed"
            })
    
    async def _handle_reload_fixtures(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle fixture configuration reload."""
        print("--🔄 Reloading fixture configuration")
        
        # TODO: Update load_fixtures_config to return proper tuple or handle None
        result = load_fixtures_config(force_reload=True)
        if result is not None:
            fixture_config, fixture_presets = result
            app_state.fixture_config = fixture_config
            app_state.fixture_presets = fixture_presets
            
            await broadcast_to_all({
                "type": "fixturesUpdated",
                "fixtures": fixture_config,
                "presets": fixture_presets
            })
        else:
            print("❌ Failed to load fixture configuration")
            await websocket.send_json({
                "type": "error",
                "message": "Failed to reload fixture configuration"
            })
    
    async def _handle_set_dmx(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle DMX channel value updates with debouncing."""
        from ..dmx_controller import set_channel, get_universe, send_artnet
        
        values = message.get("values", {})
        
        # Update pending changes
        for ch_str, val in values.items():
            try:
                ch = int(ch_str)
                val = int(val)
                if 0 <= ch <= 512 and 0 <= val <= 255:
                    self._dmx_pending_updates[ch] = val
            except (ValueError, TypeError):
                print(f"❌ Invalid DMX channel or value: {ch_str}={val}")
                continue
        
        # Cancel existing debounce task if any
        if self._dmx_update_task:
            self._dmx_update_task.cancel()
        
        # Start new debounce task
        self._dmx_update_task = asyncio.create_task(self._debounced_dmx_update())
    
    async def _debounced_dmx_update(self) -> None:
        """Execute DMX updates after debounce delay."""
        try:
            # Wait for debounce delay
            await asyncio.sleep(self._dmx_debounce_delay)
            
            # Apply all pending updates
            if self._dmx_pending_updates:
                from ..dmx_controller import set_channel, get_universe, send_artnet
                
                updates = {}
                for ch, val in self._dmx_pending_updates.items():
                    if set_channel(ch, val):
                        updates[ch] = val
                
                # Send ArtNet update
                universe_data = get_universe()
                send_artnet(0, bytes(universe_data))
                
                # Broadcast to all WebSocket clients
                await broadcast_to_all({
                    "type": "dmx_update",
                    "universe": get_universe()
                })
                
                print(f"🎛️ DMX updated: {len(updates)} channels")
                
                # Clear pending updates
                self._dmx_pending_updates.clear()
                
        except asyncio.CancelledError:
            # Task was cancelled, this is expected behavior
            pass
        except Exception as e:
            print(f"❌ Error in debounced DMX update: {e}")
        finally:
            self._dmx_update_task = None

    async def _check_ai_service_health(self) -> tuple[bool, str]:
        """Check if the AI service (Ollama) is available and return status."""
        try:
            from ..services.ollama import query_ollama_mistral_streaming
            
            # Try a simple test prompt
            test_response = ""
            async def test_callback(chunk):
                nonlocal test_response
                test_response += chunk
            
            await query_ollama_mistral_streaming("Hi", "health_check", callback=test_callback)
            return True, "AI service is ready"
        except ConnectionError:
            return False, "Cannot connect to Ollama service. Please ensure Ollama is running on http://backend-llm:11434"
        except ValueError:
            return False, "Mistral model not found. Please install it with: ollama pull mistral"
        except Exception as e:
            return False, f"AI service error: {str(e)}"


# Global WebSocket manager instance
ws_manager = WebSocketManager()


async def broadcast_to_all(message: Dict[str, Any]) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    disconnected = []
    for ws in app_state.websocket_clients:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    # Remove disconnected clients
    for ws in disconnected:
        app_state.remove_client(ws)
