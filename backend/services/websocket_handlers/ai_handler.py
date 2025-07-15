"""AI prompt handling for WebSocket service."""

from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..utils.broadcast import broadcast_to_all

# Store pending actions for each WebSocket session
_pending_actions_store = {}

async def handle_user_prompt(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle userPrompt with streaming and action proposals/confirmation flow."""
    from ...services.ollama import query_ollama_mistral_streaming
    
    prompt = message.get("text", "") or message.get("prompt", "")
    if not prompt:
        await websocket.send_json({"type": "chatResponse", "response": "No prompt provided."})
        return
    
    try:
        session_id = str(id(websocket))
        
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
                    from ...dmx_controller import get_universe
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
