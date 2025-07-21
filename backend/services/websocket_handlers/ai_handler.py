"""AI prompt handling for WebSocket service."""

from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..utils.broadcast import broadcast_to_all
from ..ollama.direct_commands_parser import DirectCommandsParser
from .action_executor import execute_confirmed_action

UI_CHAT_MODEL = "qwen3:8b"  # Default model for AI chat

# Store pending actions for each WebSocket session
_pending_actions_store = {}

# Store conversation history for each WebSocket session
_conversation_history = {}

# Create direct commands parser
_direct_commands_parser = DirectCommandsParser()

async def handle_user_prompt(websocket: WebSocket, message: Dict[str, Any]) -> None:
    """Handle userPrompt with streaming and action proposals/confirmation flow."""
    from ...services.ollama import query_ollama_streaming
    
    prompt = message.get("text", "") or message.get("prompt", "")
    if not prompt:
        await websocket.send_json({"type": "chatResponse", "response": "No prompt provided."})
        return

    # Define context separately from the prompt
    context = build_ui_context()
    print(f"ℹ️ Context: {context}")

    try:
        session_id = str(id(websocket))
        
        # Initialize conversation history for this session if not exists
        if session_id not in _conversation_history:
            _conversation_history[session_id] = []
        
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
        current_response = ""
        
        # Send chunk callback for streaming
        async def send_chunk(chunk):
            await websocket.send_json({
                "type": "chatResponseChunk", 
                "chunk": chunk
            })
        
        # Stream the AI response
        try:
            # Pass context and conversation history to the AI request
            current_response = await query_ollama_streaming(
                prompt, 
                session_id, 
                context=context, 
                conversation_history=_conversation_history[session_id],
                model=UI_CHAT_MODEL, 
                callback=send_chunk,
                websocket=websocket,  # Pass websocket for action command execution
                auto_execute_commands=True  # Enable automatic action command execution
            )
        except (ConnectionError, TimeoutError, ValueError, RuntimeError) as ai_error:
            # Handle AI service errors gracefully
            print(f"🤖 AI Service Error: {ai_error}")
            
            # Send a helpful error message as a chunk
            error_chunk = f"\n\nSorry, I'm having trouble connecting to the AI service. {str(ai_error)}\n\nPlease check that Ollama is running and the 'mistral' model is installed."
            await send_chunk(error_chunk)
        
        # End streaming
        await websocket.send_json({"type": "chatResponseEnd"})
        
        # Store the conversation in history
        _conversation_history[session_id].append({"role": "user", "content": prompt})
        _conversation_history[session_id].append({"role": "assistant", "content": current_response})
        
        # Limit conversation history to last 20 messages (10 exchanges)
        if len(_conversation_history[session_id]) > 20:
            _conversation_history[session_id] = _conversation_history[session_id][-20:]
        
        # Don't send final response - streaming chunks are sufficient
        # The frontend should handle the streaming chunks properly
        
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
        from ...services.ollama import query_ollama_streaming
        
        # Try a simple test prompt
        test_response = ""
        async def test_callback(chunk):
            nonlocal test_response
            test_response += chunk
        
        await query_ollama_streaming("Hi", "health_check", callback=test_callback)
        return True, "AI service is ready"
    except ConnectionError:
        return False, "Cannot connect to Ollama service. Please ensure Ollama is running on http://llm-service:11434"
    except ValueError:
        return False, "Mistral model not found. Please install it with: ollama pull mistral"
    except Exception as e:
        return False, f"AI service error: {str(e)}"

def _build_fixtures_context() -> str:
    """Build the context for the lighting interpretation"""
    fixture_descriptions = []
    if app_state.fixtures and hasattr(app_state.fixtures, 'fixtures'):
        fixtures_dict = app_state.fixtures.fixtures
        for fixture_id, fixture in fixtures_dict.items():
            fixture_type = "RGB PAR Light" if fixture.fixture_type == "parcan" else fixture.fixture_type
            fixture_type = "Moving Head" if fixture.fixture_type == "moving_head" else fixture_type
            fixture_descriptions.append(f"  - {fixture_type} (id: {fixture.id}) -> available actions: {', '.join(fixture.actions)}")
    else:
        raise ValueError("Fixtures not available in app_state")
    
    # Create the fixture list from the descriptions
    return "\n".join(fixture_descriptions)

def build_ui_context() -> str:
    """Build the context for the lighting interpretation"""
    song = app_state.current_song
    return f"""You are a Lighting Effects Assistant for DMX-controlled light shows synced to music.
You will receive user prompts describing lighting effects, and you will interpret these into actions using the available fixtures.

Song Interpretation Details:
{song.get_prompt()}

Capabilities:
- Understand prompts like "fade from left to right for two beats"
- Translate into actions for DMX lighting
- Effects are single or sequential actions like fade, strobe, flash, seek.
- perform many actions as needed to create the desired effect.
- Use only this fixtures: 
{_build_fixtures_context()}

Rules:
- If a user asks about non-light/music topics, reply with something silly and redirect to lighting.
    Example non-domain response:
    User: "What's the capital of Mars?"
    Assistant: "Probably Disco-topia! Anyway, shall we strobe the red heads to the beat?"

- Use ONLY the supported actions and fixtures.
- Assume all fixtures are available and ready to use.
- Lights are located in a venue with a stage and audience (not in a car or other setting)
- Combine multiple actions to create complex effects when needed.
- Please respond in English and keep your responses short.
- If you don't understand a prompt, ask for clarification.
- When no exact start time is provided, use the current song's closest beat time.
- actions should be in the EXACTLY format:
   - "#action <action> <fixture_id> at <start_time> for <duration>" -> example: "#action fade moving_head_1 at 1.21s for 2s"
   - each action should be a single line starting with #action and not contain any other text.
- Complex effects may require multiple actions, so you can perform many actions as needed to create the desired effect.
- DMX Fixtures doesn't have logic for complex effects, so you must perform each action separately.
"""
