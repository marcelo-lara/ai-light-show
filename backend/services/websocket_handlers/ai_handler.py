"""AI prompt handling for WebSocket service."""

from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..utils.broadcast import broadcast_to_all
from ..ollama.direct_commands_parser import DirectCommandsParser
from .action_executor import execute_confirmed_action

# Store pending actions for each WebSocket session
_pending_actions_store = {}

# Create direct commands parser
_direct_commands_parser = DirectCommandsParser()

async def handle_user_prompt(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle userPrompt with streaming and action proposals/confirmation flow."""
    from ...services.ollama import query_ollama_mistral_streaming
    
    prompt = message.get("text", "") or message.get("prompt", "")
    if not prompt:
        await websocket.send_json({"type": "chatResponse", "response": "No prompt provided."})
        return
    
    try:
        session_id = str(id(websocket))
        
        # Check if this is a direct command (starts with #)
        if prompt.strip().startswith("#"):
            await _handle_direct_command(websocket, prompt)
            return

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
        except (ConnectionError, TimeoutError, ValueError, RuntimeError) as ai_error:
            # Handle AI service errors gracefully
            print(f"🤖 AI Service Error: {ai_error}")
            
            # Send a helpful error message as a chunk
            error_chunk = f"\n\nSorry, I'm having trouble connecting to the AI service. {str(ai_error)}\n\nPlease check that Ollama is running and the 'mistral' model is installed."
            await send_chunk(error_chunk)
        
        # End streaming
        await websocket.send_json({"type": "chatResponseEnd"})
        
        # Send final response for any clients that didn't process the streaming chunks
        await websocket.send_json({
            "type": "chatResponse",
            "response": full_ai_response
        })
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
            error_message = "Can't connect to the AI service. Please make sure Ollama is running on http://llm-server:11434"
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
            if app_state.current_song_file:
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
        from ...services.ollama import query_ollama_mistral_streaming
        
        # Try a simple test prompt
        test_response = ""
        async def test_callback(chunk):
            nonlocal test_response
            test_response += chunk
        
        await query_ollama_mistral_streaming("Hi", "health_check", callback=test_callback)
        return True, "AI service is ready"
    except ConnectionError:
        return False, "Cannot connect to Ollama service. Please ensure Ollama is running on http://llm-server:11434"
    except ValueError:
        return False, "Mistral model not found. Please install it with: ollama pull mistral"
    except Exception as e:
        return False, f"AI service error: {str(e)}"
