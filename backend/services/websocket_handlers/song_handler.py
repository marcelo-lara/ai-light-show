"""Song-related WebSocket handlers."""

import asyncio
from pathlib import Path
from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from shared.models.song_metadata import SongMetadata, Section
from ...config import SONGS_DIR
from ..dmx.dmx_canvas import DmxCanvas
from ..utils.broadcast import broadcast_to_all
from ...services.actions_service import ActionsService

async def handle_load_song(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle song loading."""
    song_file = message["file"]
    print(f"🎶 Loading song: {song_file}")
    
    app_state.current_song_file = song_file
    app_state.current_song = SongMetadata(song_file, songs_folder=str(SONGS_DIR))

    # Re-initialize the DmxCanvas with the new song duration plus 2 seconds for final effects
    song_duration = app_state.current_song.duration
    canvas_duration = song_duration + 2.0  # Add 2 seconds for final effects
    if song_duration > 0:
        print(f"🎛️ Re-initializing DMX Canvas with duration: {canvas_duration:.2f}s (song: {song_duration:.2f}s + 2s for effects)")
        app_state.reset_dmx_canvas(fps=44, duration=canvas_duration)
    else:
        # Fallback to audio file length or default duration
        from mutagen.mp3 import MP3
        try:
            audio = MP3(song_file)
            song_duration = audio.info.length
            canvas_duration = song_duration + 2.0  # Add 2 seconds for final effects
            print(f"⏱️ Using audio file duration: {canvas_duration:.2f}s (song: {song_duration:.2f}s + 2s for effects)")
        except Exception as e:
            print(f"⚠️ Failed to get audio duration: {e}, using default")
            song_duration = 300.0  # 5 minute default
            canvas_duration = song_duration + 2.0  # Add 2 seconds for final effects
        
        app_state.reset_dmx_canvas(fps=44, duration=canvas_duration)
        

    # Load actions for the song
    actions = []
    try:
        from ...models.actions_sheet import ActionsSheet
        song_name = Path(song_file).stem
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        actions = [action.to_dict() for action in actions_sheet.actions]
        print(f"📋 Loaded {len(actions)} actions for {song_name}")

        # render actions to DMX canvas
        dmx_canvas = app_state.dmx_canvas  # Use the singleton instance from app_state
        if app_state.fixtures is None:
            raise ValueError("Fixtures are not initialized in app_state")
        actions_service = ActionsService(app_state.fixtures, dmx_canvas)
        actions_service.render_actions_to_canvas(actions_sheet)


    except Exception as e:
        print(f"❌ Error loading actions: {e}")

    # Send song loaded message
    await websocket.send_json({
        "type": "songLoaded",
        "metadata": app_state.current_song.to_dict(),
        "message": f"Song loaded - DMX Canvas initialized with {song_duration:.2f}s duration"
    })
    
    # Broadcast actions update to all clients
    await broadcast_to_all({
        "type": "actionsUpdate",
        "actions": actions
    })

async def handle_save_arrangement(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle saving song arrangement."""
    arrangement = message["arrangement"]
    if app_state.current_song is not None:
        # Convert arrangement dictionary to list of Section objects
        app_state.current_song.arrangement = [
            Section(**v) for k, v in arrangement.items()
        ]
        app_state.current_song.save()
    else:
        print("No song object loaded; cannot save arrangement.")

async def handle_save_key_moments(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle saving song key moments."""
    key_moments = message["key_moments"]
    if app_state.current_song is not None:
        app_state.current_song.key_moments = key_moments
        app_state.current_song.save()
        print(f"✅ Saved {len(key_moments)} key moments for {app_state.current_song.song_name}")
    else:
        print("No song object loaded; cannot save key moments.")

async def handle_save_light_plan(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle saving song light plan."""
    light_plan = message["light_plan"]
    if app_state.current_song is not None:
        app_state.current_song.light_plan = light_plan
        app_state.current_song.save()
        print(f"✅ Saved {len(light_plan)} light plan items for {app_state.current_song.song_name}")
    else:
        print("No song object loaded; cannot save light plan.")

async def handle_analyze_song(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle song analysis using the standalone song analysis service."""
    from ..song_analysis_client import SongAnalysisClient
    
    if not app_state.current_song:
        print("❌ No song loaded for analysis")
        await websocket.send_json({
            "type": "analyzeResult",
            "status": "error",
            "message": "No song loaded for analysis"
        })
        return

    try:
        # Use the standalone song analysis service
        async with SongAnalysisClient() as client:
            # First check if service is healthy
            health = await client.health_check()
            if health.get("status") != "healthy":
                raise Exception(f"Song analysis service is not healthy: {health.get('error', 'Unknown error')}")
            
            # Perform analysis using song name instead of full path
            song_name = Path(app_state.current_song.mp3_path).stem
            result = await client.analyze_song(
                song_name=song_name,
                reset_file=True,
                debug=False
            )
            
            if result.get("status") == "success":
                # Update the current song with analysis results
                metadata = result.get("metadata", {})
                
                # FIXME: current song should be loaded, not recreated
                app_state.current_song.bpm = metadata.get("bpm", app_state.current_song.bpm)
                app_state.current_song.duration = metadata.get("duration", app_state.current_song.duration)
                app_state.current_song.beats = metadata.get("beats", [])
                app_state.current_song.patterns = metadata.get("patterns", [])
                app_state.current_song.chords = metadata.get("chords", [])
                app_state.current_song.analysis = metadata.get("analysis", [])
                app_state.current_song.arrangement = metadata.get("arrangement", [])
                app_state.current_song.key_moments = metadata.get("key_moments", [])
                
                # Save updated metadata
                app_state.current_song.save()
                
                await websocket.send_json({
                    "type": "analyzeResult",
                    "status": "ok",
                    "metadata": app_state.current_song.to_dict()
                })
            else:
                raise Exception(result.get("message", "Analysis failed"))
                
    except Exception as e:
        print(f"❌ Song analysis failed: {str(e)}")
        await websocket.send_json({
            "type": "analyzeResult",
            "status": "error",
            "message": f"Analysis failed: {str(e)}"
        })
