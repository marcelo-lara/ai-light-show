"""AI prompt handling for WebSocket service."""

import os
from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..utils.broadcast import broadcast_to_all
from ..direct_commands import DirectCommandsParser
from .action_executor import execute_confirmed_action
from ..agents.ui_agent import UIAgent

# Store pending actions for each WebSocket session
_pending_actions_store = {}

# Store conversation history for each WebSocket session
_conversation_history = {}

# Create direct commands parser
_direct_commands_parser = DirectCommandsParser()

async def handle_user_prompt(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle userPrompt with streaming and action proposals/confirmation flow."""
    
    prompt = message.get("text", "") or message.get("prompt", "")
    if not prompt:
        await websocket.send_json({"type": "chatResponse", "response": "No prompt provided."})
        return

    # Check if this is a direct command (starts with #)
    if prompt.strip().startswith("#"):
        await _handle_direct_command(websocket, prompt)
        return

    try:
        session_id = str(id(websocket))

        # Initialize conversation history for this session if not exists
        if session_id not in _conversation_history:
            _conversation_history[session_id] = []

        # Check if this is a confirmation message for pending actions
        pending_actions = _pending_actions_store.get(session_id)
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
                if any_success:
                    from backend.dmx_controller import get_universe
                    current_universe = get_universe()
                    await broadcast_to_all({
                        "type": "dmxCanvasUpdated",
                        "universe": list(current_universe),
                        "message": "DMX Canvas updated by AI actions"
                    })
                
                # Clear pending actions
                if session_id in _pending_actions_store:
                    del _pending_actions_store[session_id]
                return
                
            elif is_rejection:
                await websocket.send_json({
                    "type": "chatResponse", 
                    "response": "Actions cancelled.",
                    "action_proposals": []
                })
                
                # Clear pending actions
                if session_id in _pending_actions_store:
                    del _pending_actions_store[session_id]
                return
        
        # Start streaming response
        await websocket.send_json({"type": "chatResponseStart"})
        
        # Collect full response for action processing
        current_response = ""
        
        # Send chunk callback for streaming
        async def send_chunk(chunk):
            nonlocal current_response
            current_response += chunk
            await websocket.send_json({
                "type": "chatResponseChunk", 
                "chunk": chunk
            })

        # Create UI Agent and run it
        try:
            ui_agent = UIAgent()
            
            # Prepare input data for the agent
            input_data = {
                "prompt": prompt,
                "callback": send_chunk,
                "websocket": websocket,
                "conversation_history": _conversation_history[session_id]
            }
            
            # Run the agent
            result = await ui_agent.run(input_data)
            
            if result["success"]:
                current_response = result["response"]
            else:
                error_message = f"Sorry, I encountered an error: {result['error']}"
                await send_chunk(error_message)
                current_response = error_message
                
        except Exception as ai_error:
            # Handle AI service errors gracefully
            print(f"🤖 AI Service Error: {ai_error}")
            
            # Send a helpful error message as a chunk
            error_chunk = f"\n\nSorry, I'm having trouble connecting to the AI service. {str(ai_error)}\n\nPlease check that Ollama is running and the 'cogito:8b' model is installed."
            await send_chunk(error_chunk)
            current_response = error_chunk
        
        # End streaming
        await websocket.send_json({"type": "chatResponseEnd"})
        
        # After streaming is complete, check for actions in the response and send to frontend
        await _process_response_actions(current_response, websocket)
        
        # Store the conversation in history
        _conversation_history[session_id].append({"role": "user", "content": prompt})
        _conversation_history[session_id].append({"role": "assistant", "content": current_response})

        # Limit conversation history to last 20 messages (10 exchanges)
        if len(_conversation_history[session_id]) > 20:
            _conversation_history[session_id] = _conversation_history[session_id][-20:]

        # Update status to complete
        await broadcast_to_all({
            "type": "chatStatus",
            "status": "ready"
        })

    except Exception as e:
        print(f"❌ Error in handle_user_prompt: {e}")

        # Provide user-friendly error messages
        error_message = "Sorry, I'm having trouble connecting to the AI service right now. Please check if the Ollama service is running and try again."

        # Check for specific error types
        if "Connection" in str(e) or "connect" in str(e).lower():
            error_message = "Can't connect to the AI service. Please make sure Ollama is running on http://llm-service:11434"
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

async def _handle_direct_command(websocket: WebSocket, command: str) -> None:
    """
    Handle direct action commands that bypass the LLM.
    
    Args:
        websocket (WebSocket): The WebSocket connection
        command (str): The command text (starting with #action)
    """
    try:
        # Parse and execute the command (must await async)
        success, message, additional_data = await _direct_commands_parser.parse_command(command, websocket=websocket)
        
        # Send the response to the user
        await websocket.send_json({
            "type": "chatResponse",
            "response": f"**Direct Command Result**: {message}",
            "action_proposals": []
        })
        
        # If command execution was successful, update clients
        if success:
            # If command execution generated universe updates to broadcast (like render command)
            if additional_data and "universe" in additional_data:
                await broadcast_to_all({
                    "type": "dmxCanvasUpdated",
                    "universe": additional_data["universe"],
                    "message": additional_data.get("message", "DMX Canvas updated by direct command")
                })
                
            # Always broadcast actions update to refresh the UI for any successful direct command
            # or if the additional_data indicates actions were updated
            if app_state.current_song_file and (additional_data is None or additional_data.get("actions_updated", False)):
                from pathlib import Path
                from ...models.actions_sheet import ActionsSheet
                
                # Get current actions
                song_name = Path(app_state.current_song_file).stem
                actions_sheet = ActionsSheet(song_name)
                actions_sheet.load_actions()
                
                # Log the actions update
                action_count = len(actions_sheet.actions)
                print(f"📊 Broadcasting actions update: {action_count} actions for song '{song_name}'")
                
                # Broadcast actions update
                await broadcast_to_all({
                    "type": "actionsUpdate",
                    "actions": [action.to_dict() for action in actions_sheet.actions]
                })
        
    except Exception as e:
        print(f"❌ Error in _handle_direct_command: {e}")
        await websocket.send_json({
            "type": "chatResponse",
            "response": f"**Direct Command Error**: {str(e)}"
        })

async def check_ai_service_health() -> tuple[bool, str]:
    """Check if the AI service (Ollama) is available and return status."""
    try:
        # Create a UI agent for health check
        ui_agent = UIAgent()
        
        # Simple test to see if we can create context (this tests song/fixtures access)
        # We'll catch the specific error about no song being loaded
        try:
            test_context = ui_agent._build_context({})
        except ValueError as ve:
            if "No song is currently loaded" in str(ve):
                # This is expected when no song is loaded, but it means the agent setup is working
                return True, "AI service is ready (no song loaded)"
            else:
                raise ve
        except AttributeError as ae:
            # Handle case where song object exists but is not properly initialized
            if "_title" in str(ae) or "_beats" in str(ae) or "song" in str(ae).lower():
                return True, "AI service is ready (song not fully loaded)"
            else:
                raise ae
        
        # If we got here, we have a song loaded and context built successfully
        return True, "AI service is ready"
        
    except ConnectionError:
        return False, "Cannot connect to Ollama service. Please ensure Ollama is running on http://llm-service:11434"
    except ValueError as ve:
        if "not found" in str(ve) and "model" in str(ve):
            return False, f"Model not found. Please install it with: ollama pull {ui_agent.model_name}"
        else:
            return False, f"AI service error: {str(ve)}"
    except Exception as e:
        return False, f"AI service error: {str(e)}"

async def _process_response_actions(response: str, websocket: WebSocket) -> None:
    """
    Process the AI response to detect and save any action commands, 
    then broadcast the updated actions to the frontend.
    
    Args:
        response (str): The complete AI response text
        websocket (WebSocket): The WebSocket connection for sending updates
    """
    try:
        # Extract action commands from the response (lines starting with #action or #)
        action_lines = []
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('#action') or (line.startswith('#') and any(word in line for word in ['flash', 'strobe', 'fade', 'seek', 'arm'])):
                action_lines.append(line)
        
        if not action_lines:
            print("📝 No action commands found in AI response")
            return
        
        print(f"🎭 Found {len(action_lines)} action commands in AI response")
        
        # Process each action command
        actions_added = 0
        for action_line in action_lines:
            try:
                # Parse and execute the action command
                success, message, additional_data = await _direct_commands_parser.parse_command(action_line, websocket=websocket)
                if success:
                    actions_added += 1
                    print(f"✅ Action executed: {action_line}")
                else:
                    print(f"❌ Action failed: {action_line} -> {message}")
            except Exception as e:
                print(f"❌ Error processing action '{action_line}': {e}")
        
        # If actions were added successfully, broadcast the updated actions to frontend
        if actions_added > 0 and app_state.current_song_file:
            from pathlib import Path
            from ...models.actions_sheet import ActionsSheet
            
            # Get current actions
            song_name = Path(app_state.current_song_file).stem
            actions_sheet = ActionsSheet(song_name)
            actions_sheet.load_actions()
            
            # Log the actions update
            action_count = len(actions_sheet.actions)
            print(f"📊 Broadcasting actions update: {action_count} total actions for song '{song_name}' (added {actions_added} new)")
            
            # IMPORTANT: Render actions to canvas so they appear on the main canvas
            try:
                # Automatically render actions to canvas after adding them
                render_success, render_message, render_data = await _direct_commands_parser.parse_command("#render", websocket=websocket)
                if render_success:
                    print(f"✅ Actions rendered to canvas: {render_message}")
                else:
                    print(f"⚠️ Failed to render actions to canvas: {render_message}")
            except Exception as render_error:
                print(f"❌ Error rendering actions to canvas: {render_error}")
            
            # Broadcast actions update to all clients
            await broadcast_to_all({
                "type": "actionsUpdate",
                "actions": [action.to_dict() for action in actions_sheet.actions]
            })
            
            # Also broadcast DMX canvas update
            from backend.dmx_controller import get_universe
            current_universe = get_universe()
            await broadcast_to_all({
                "type": "dmxCanvasUpdated",
                "universe": list(current_universe),
                "message": f"DMX Canvas updated by AI actions ({actions_added} actions added)"
            })
        
    except Exception as e:
        print(f"❌ Error in _process_response_actions: {e}")
