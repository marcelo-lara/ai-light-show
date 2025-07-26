"""Action handling for WebSocket service."""

from typing import Dict, Any, List, Optional
from fastapi import WebSocket
from pathlib import Path
import json
from ...models.app_state import app_state
from ..utils.broadcast import broadcast_to_all
from ...models.actions_sheet import ActionsSheet, ActionModel
from ...services.actions_service import ActionsService

async def handle_add_action(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """
    Handle addAction message to add an action to the current song's action sheet.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        message (Dict[str, Any]): The message containing action details
    """
    # Validate required fields
    fixture_id = message.get("fixture_id")
    action = message.get("action")
    parameters = message.get("parameters", {})
    
    if not fixture_id or not action:
        await websocket.send_json({
            "type": "error",
            "message": "Missing required fields: fixture_id and action"
        })
        return
    
    # Check if a song is loaded
    if not app_state.current_song_file:
        await websocket.send_json({
            "type": "error",
            "message": "No song is currently loaded"
        })
        return
    
    # Check if fixture exists
    if app_state.fixtures is None or fixture_id not in app_state.fixtures.fixtures:
        await websocket.send_json({
            "type": "error",
            "message": f"Fixture '{fixture_id}' not found"
        })
        return
    
    # Check if action is supported by fixture
    fixture = app_state.fixtures.fixtures[fixture_id]
    if action not in fixture.actions:
        await websocket.send_json({
            "type": "error",
            "message": f"Action '{action}' not supported by fixture '{fixture_id}'"
        })
        return
    
    # Clean parameters - remove empty values
    cleaned_parameters = {}
    for key, value in parameters.items():
        # Skip empty strings, None values, or empty lists
        if value is not None and value != "" and value != []:
            cleaned_parameters[key] = value
    
    try:
        # Create a new action model
        start_time = float(cleaned_parameters.get("start_time", 0.0))
        duration = float(cleaned_parameters.get("duration", 1.0))
        
        # Remove start_time from parameters as it's handled separately
        if "start_time" in cleaned_parameters:
            del cleaned_parameters["start_time"]
        
        # Remove duration from parameters as it's handled separately
        if "duration" in cleaned_parameters:
            del cleaned_parameters["duration"]
        
        # Create the action model
        new_action = ActionModel(
            action=action,
            fixture_id=fixture_id,
            parameters=cleaned_parameters,
            start_time=start_time,
            duration=duration
        )
        
        # Get or create the actions sheet
        song_name = Path(app_state.current_song_file).stem
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        
        # Add the action to the sheet
        actions_sheet.add_action(new_action)
        
        # Save the actions
        actions_sheet.save_actions()
        
        # Render the actions to the canvas
        if app_state.dmx_canvas is not None and app_state.fixtures is not None:
            actions_service = ActionsService(app_state.fixtures, app_state.dmx_canvas)
            render_success = actions_service.render_actions_to_canvas(actions_sheet, clear_first=False)
            
            if render_success:
                # Get universe for broadcast
                from backend.dmx_controller import get_universe
                universe = get_universe()
                
                # Broadcast DMX update to all clients
                await broadcast_to_all({
                    "type": "dmxCanvasUpdated",
                    "universe": list(universe),
                    "message": f"DMX Canvas updated with new action: {action} on {fixture_id}"
                })
        
        # Send success response
        await websocket.send_json({
            "type": "actionAdded",
            "message": f"Added {action} action to {fixture_id} at {start_time}s",
            "action": new_action.to_dict()
        })
        
        # Broadcast actions update to all clients
        actions = [action.to_dict() for action in actions_sheet.actions]
        await broadcast_to_all({
            "type": "actionsUpdate",
            "actions": actions
        })
        
    except Exception as e:
        print(f"❌ Error adding action: {e}")
        await websocket.send_json({
            "type": "error",
            "message": f"Error adding action: {str(e)}"
        })
