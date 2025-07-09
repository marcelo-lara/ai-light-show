"""WebSocket service for real-time communication."""

import asyncio
import time
from typing import Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect
from ..models.app_state import app_state
from ..chaser_utils import get_chasers
from ..fixture_utils import load_fixtures_config
from ..models.song_metadata import SongMetadata, Section
from ..timeline_engine import render_timeline
from ..config import SONGS_DIR
from .cue_service import cue_manager


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
            "getCues": self._handle_get_cues,
            "addCue": self._handle_add_cue,
            "updateCues": self._handle_update_cues,
            "updateCue": self._handle_update_cue,
            "deleteCue": self._handle_delete_cue,
            "previewDmx": self._handle_preview_dmx,
            "saveArrangement": self._handle_save_arrangement,
            "insertChaser": self._handle_insert_chaser,
            "analyzeSong": self._handle_analyze_song,
            "reloadFixtures": self._handle_reload_fixtures,
            "setDmx": self._handle_set_dmx,
            "userPrompt": self._handle_user_prompt,
        }

    async def _handle_user_prompt(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle userPrompt by sending to ollama/mistral and streaming the response."""
        from ..ai.ollama_client import query_ollama_mistral_streaming
        prompt = message.get("text", "") or message.get("prompt", "")
        if not prompt:
            await websocket.send_json({"type": "chatResponse", "response": "No prompt provided."})
            return
        
        try:
            session_id = str(id(websocket))
            
            # Send chunk callback
            async def send_chunk(chunk):
                await websocket.send_json({
                    "type": "chatResponseChunk", 
                    "chunk": chunk
                })
            
            # Start streaming
            await websocket.send_json({"type": "chatResponseStart"})
            
            # Stream the response
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: asyncio.run(
                query_ollama_mistral_streaming(prompt, session_id, callback=send_chunk)
            ))
            
            # End streaming
            await websocket.send_json({"type": "chatResponseEnd"})
            
        except Exception as e:
            await websocket.send_json({"type": "chatResponse", "response": f"Error: {e}"})
    
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
            "presets": app_state.fixture_presets,
            "chasers": get_chasers()
        })
    
    async def disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection."""
        app_state.remove_client(websocket)
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
        if "isPlaying" in message:
            app_state.playback.is_playing = message["isPlaying"]
        if "currentTime" in message:
            app_state.playback.playback_time = message["currentTime"]
            if app_state.playback.is_playing:
                app_state.playback.start_monotonic = time.monotonic() - app_state.playback.playback_time

        await websocket.send_json({
            "type": "syncAck",
            "isPlaying": app_state.playback.is_playing,
            "currentTime": app_state.playback.playback_time
        })
    
    async def _handle_load_song(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle song loading."""
        song_file = message["file"]
        print(f"🎶 Loading song: {song_file}")
        
        app_state.current_song_file = song_file
        app_state.current_song = SongMetadata(song_file, songs_folder=str(SONGS_DIR))
        
        # Load cues for this song
        cue_manager.load_cues(song_file)

        await websocket.send_json({
            "type": "songLoaded",
            "metadata": app_state.current_song.to_dict(),
            "cues": cue_manager.cue_list,
        })
        
        # Render timeline
        bpm = app_state.current_song.bpm
        render_timeline(
            app_state.fixture_config, 
            app_state.fixture_presets, 
            cues=cue_manager.cue_list, 
            current_song=app_state.current_song_file, 
            bpm=bpm
        )
    
    async def _handle_get_cues(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle cue list request."""
        print(f"🔍 Fetching cues for {cue_manager.current_song_file}")
        await websocket.send_json({
            "type": "cuesUpdated",
            "cues": cue_manager.cue_list
        })
    
    async def _handle_add_cue(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle adding a new cue."""
        cue = message["cue"]
        cue_manager.add_cue(cue)
        print(f"📝 Added new cue: {cue}")
        
        cue_manager.save_cues()
        
        await broadcast_to_all({
            "type": "cuesUpdated",
            "cues": cue_manager.cue_list
        })
    
    async def _handle_update_cues(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle bulk cue updates."""
        cues = message["cues"]
        cue_manager.update_cues(cues)
        print(f"📝 Updated cues: {len(cues)} cues")
        
        cue_manager.save_cues()
        
        await broadcast_to_all({
            "type": "cuesUpdated",
            "cues": cue_manager.cue_list
        })
    
    async def _handle_update_cue(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle single cue update."""
        updated = message["cue"]
        for i, c in enumerate(cue_manager.cue_list):
            if c["fixture"] == updated["fixture"] and c["time"] == updated["time"]:
                cue_manager.cue_list[i] = updated
                print(f"📝 Updated cue: {updated}")
                break

        cue_manager.save_cues()
        
        await broadcast_to_all({
            "type": "cuesUpdated",
            "cues": cue_manager.cue_list
        })
    
    async def _handle_delete_cue(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle cue deletion."""
        cue = message["cue"]

        if "chaser_id" in cue:
            cid = cue["chaser_id"]
            cue_manager.delete_cue_by_chaser_id(cid)
            print(f"🗑️ Deleted chaser group '{cid}'")
        else:
            cue_manager.delete_cue(cue["fixture"], cue["time"])

        cue_manager.save_cues()
        
        await broadcast_to_all({
            "type": "cuesUpdated",
            "cues": cue_manager.cue_list
        })
    
    async def _handle_preview_dmx(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle DMX preview."""
        cue = message["cue"]
        cue["time"] = 0  # Set time to 0 for preview

        # Render a tiny timeline with only this cue
        bpm = 120  # or use current song bpm
        fps = 30
        tmp_timeline = render_timeline(
            app_state.fixture_config,
            app_state.fixture_presets,
            cues=[cue],
            current_song="__preview__",
            bpm=bpm,
            fps=fps
        )

        print(f"🔍 Previewing DMX for cue: {cue}")

        # Immediately execute the DMX for first few frames (simulate preview)
        from ..dmx_controller import send_artnet
        for frame in tmp_timeline:
            send_artnet(tmp_timeline[frame])
            await asyncio.sleep(1 / fps)
    
    async def _handle_save_arrangement(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle saving song arrangement."""
        arrangement = message["arrangement"]
        if app_state.current_song is not None:
            app_state.current_song.arrangement = {k: Section(**v) for k, v in arrangement.items()}
            app_state.current_song.save()
        else:
            print("No song object loaded; cannot save arrangement.")
    
    async def _handle_insert_chaser(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle chaser insertion."""
        from ..chaser_utils import expand_chaser_template
        
        chaser_name = message["chaser"]
        insert_time = message["time"]
        user_params = message.get("parameters", {})
        chaser_id = message.get("chaser_id")

        bpm = app_state.song_metadata.get("bpm", 120)
        new_cues = expand_chaser_template(chaser_name, insert_time, bpm)

        for cue in new_cues:
            cue["parameters"].update(user_params)
            cue["chaser"] = chaser_name
            cue["chaser_id"] = chaser_id

        # Add new cues to the cue manager
        for cue in new_cues:
            cue_manager.add_cue(cue)
        
        cue_manager.save_cues()

        await broadcast_to_all({
            "type": "cuesUpdated",
            "cues": cue_manager.cue_list
        })
    
    async def _handle_analyze_song(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle song analysis."""
        from ..song_analyze import song_analyze, build_test_cues
        
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

        create_test = message.get("renderTestCues", False)
        if create_test:
            print("👁️‍🗨️ Generating cues from song analysis")
            cues = build_test_cues(app_state.current_song)
            cue_manager.update_cues(cues)
            render_timeline(
                app_state.fixture_config, 
                app_state.fixture_presets, 
                cues=cue_manager.cue_list, 
                current_song=app_state.current_song_file, 
                bpm=app_state.current_song.bpm
            )

            await broadcast_to_all({
                "type": "cuesUpdated",
                "cues": cue_manager.cue_list
            })
    
    async def _handle_reload_fixtures(self, websocket: WebSocket, message: Dict[str, Any]) -> None:
        """Handle fixture configuration reload."""
        print("--🔄 Reloading fixture configuration")
        fixture_config, fixture_presets, chasers = load_fixtures_config(force_reload=True)
        
        app_state.fixture_config = fixture_config
        app_state.fixture_presets = fixture_presets
        app_state.chasers = chasers
        
        await broadcast_to_all({
            "type": "fixturesUpdated",
            "fixtures": fixture_config,
            "presets": fixture_presets,
            "chasers": chasers
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
                send_artnet()
                
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
