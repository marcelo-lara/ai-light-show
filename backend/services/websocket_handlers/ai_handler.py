"""AI prompt handling for WebSocket service."""

import os
from typing import Dict, Any
from fastapi import WebSocket
from ...models.app_state import app_state
from ..utils.broadcast import broadcast_to_all
from ..direct_commands import DirectCommandsParser
from .action_executor import execute_confirmed_action
from ...services.agents import ContextBuilderAgent, LightingPlannerAgent, EffectTranslatorAgent
from ...services.agents.context_builder import PipelineState

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

    # Check if this is a direct command (starts with #)
    if prompt.strip().startswith("#"):
        await _handle_direct_command(websocket, prompt)
        return

    # Check if this is a direct agent request (starts with :)
    if prompt.strip().startswith(":"):
        await _handle_agent_request(websocket, prompt)
        return

    # Define context separately from the prompt
    context = build_ui_context()

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

async def _handle_agent_request(websocket: WebSocket, command: str) -> None:
    """
    Handle agent requests that involve the LLM.
    """

    agent_handlers = {
        "fx": EffectTranslatorAgent,
        "context_builder": ContextBuilderAgent,
        "lighting_planner": LightingPlannerAgent
    }

    agent = command.strip().lstrip(":").split(" ")[0].lower()
    prompt = " ".join(command.strip().lstrip(":").split(" ")[1:])

    if agent not in agent_handlers:
        await websocket.send_json({
            "type": "chatResponse",
            "response": f"Unknown agent '{agent}'. Available agents: {', '.join(agent_handlers.keys())}"
        })
        return

    try:
        # Call the appropriate agent handler and execute the prompt
        agent_class = agent_handlers[agent]
        agent_instance = agent_class()
        
        # Show processing message to the user
        await websocket.send_json({
            "type": "chatResponseStart"
        })
        
        if agent == "context_builder":
            # Create a pipeline state with empty segment for direct context building
            segment = {"name": "Custom", "start": 0.0, "end": 0.0, "features": {}}
            state = PipelineState(segment=segment, context_summary="", actions=[], dmx=[])
            
            # Either use the prompt as context or generate context based on the prompt
            if prompt.strip():
                result = agent_instance.get_context(prompt)
            else:
                result = agent_instance.run(state)
                result = result.get("context_summary", "No context generated")
                
        elif agent == "lighting_planner":
            # Generate lighting actions based on prompt
            context = prompt
            result = agent_instance.get_lighting_plan(context)
            
        elif agent == "fx" or agent == "effect_translator":
            # Generate DMX commands for the prompt
            actions = [{"type": "custom", "description": prompt, "start": 0.0, "duration": 5.0}]
            result = agent_instance.translate_actions(actions)
        
        # Format the response for the frontend
        if isinstance(result, dict) or isinstance(result, list):
            import json
            response = f"**{agent.capitalize()} Result**:\n```json\n{json.dumps(result, indent=2)}\n```"
        else:
            response = f"**{agent.capitalize()} Result**:\n{result}"
        
        # Send the response to the frontend
        await websocket.send_json({
            "type": "chatResponseEnd"
        })
        
        await websocket.send_json({
            "type": "chatResponse",
            "response": response
        })
    except Exception as e:
        print(f"❌ Error in _handle_agent_request: {e}")
        
        # End the response stream if it was started
        await websocket.send_json({
            "type": "chatResponseEnd"
        })
        
        await websocket.send_json({
            "type": "chatResponse",
            "response": f"**Agent Request Error**: {str(e)}"
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

def build_ui_context() -> str:
    """Build the context for the lighting interpretation using Jinja2 templates"""
    from pathlib import Path
    from jinja2 import Environment, FileSystemLoader
    
    # Setup Jinja2 environment
    prompts_dir = Path(__file__).parent.parent / "agents" / "prompts"
    jinja_env = Environment(
        loader=FileSystemLoader(prompts_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # Load the template
    template = jinja_env.get_template('ui_context.j2')
    
    # Prepare template variables
    song = app_state.current_song
    song_data = {}
    
    # Handle case when no song is loaded
    if song is None:
        raise ValueError("No song is currently loaded. Please load a song to build the UI context.")

    # Extract song data for template
    song_data = {
        "title": getattr(song, 'song_name', 'Unknown'),
        "bpm": getattr(song, 'bpm', 0),
        "duration": getattr(song, 'duration', 0),
        "arrangement": getattr(song, 'sections', []),
        "beats": song.get_beats_array(),
        "key_moments": getattr(song, 'key_moments', [])
    }
    
    # Prepare fixtures data
    fixtures = []
    if app_state.fixtures and hasattr(app_state.fixtures, 'fixtures'):
        fixtures_dict = app_state.fixtures.fixtures
        for fixture_id, fixture in fixtures_dict.items():
            fixtures.append({
                "id": fixture.id,
                "type": fixture.fixture_type,
                "effects": fixture.actions
            })
    
    # Render the template with context
    _prompt = template.render(song=song_data, fixtures=fixtures)
    
    # save the prompt to a file for debugging
    try:
        _ffile = os.path.join(app_state.current_song.data_folder, "ui_context_debug.txt")
        with open(_ffile, "w") as f:
            f.write(_prompt)
    except Exception as e:
        print(f"Error saving UI context prompt to file: {e}")

    return _prompt
