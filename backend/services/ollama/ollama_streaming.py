"""Simplified streaming functionality for Ollama API."""

import aiohttp
import asyncio
import json
import re
from typing import Optional, Callable, Any

async def query_ollama_streaming(
    prompt: str, 
    session_id: str = "default", 
    model: str = "mistral",
    base_url: str = "http://llm-service:11434", 
    callback: Optional[Callable[[str], Any]] = None,
    context: Optional[str] = None,
    conversation_history: Optional[list] = None,
    temperature: float = 0.7,
    websocket = None,  # WebSocket for executing direct commands
    auto_execute_commands: bool = True  # Whether to auto-execute #action commands
) -> str:
    """Send a prompt to Ollama and call callback for each chunk.
    
    Args:
        prompt: The user prompt to send
        session_id: Session identifier
        model: Ollama model to use
        base_url: Ollama service URL
        callback: Function to call for each chunk
        context: System context for the conversation
        conversation_history: Previous messages in the conversation
        temperature: Model temperature setting
        websocket: WebSocket connection for executing direct commands
        auto_execute_commands: Whether to automatically execute #action commands found in the response
    
    Returns:
        The complete response from the model
    """
    
    try:
        print(f"🤖 Starting Ollama/{model} streaming request for session {session_id}")

        # Include context in the request data if provided
        request_data = {
            "model": model, 
            "messages": [],
            "temperature": temperature,
            "stream": True,  # Enable streaming
            "think": True  # Enable thinking mode for the model
        }
        
        # Add system context if provided
        if context:
            request_data["messages"].append({"role": "system", "content": context})
        
        # Add conversation history if provided (properly implement chat history)
        if conversation_history:
            # Add the conversation history to maintain context
            request_data["messages"].extend(conversation_history)
            
        # Add current user prompt
        request_data["messages"].append({"role": "user", "content": prompt})
        
        # Debug: Print the number of messages being sent and show structure
        print(f"🤖 Sending {len(request_data['messages'])} messages to Ollama")
        for i, msg in enumerate(request_data['messages']):
            role = msg.get('role', 'unknown')
            content_preview = msg.get('content', '')[:50] + '...' if len(msg.get('content', '')) > 50 else msg.get('content', '')
            print(f"  [{i}] {role}: {content_preview}")
        
        async with aiohttp.ClientSession() as session:
            print(f"🤖 Connecting to Ollama at {base_url}")
            async with session.post(
                f"{base_url}/api/chat",
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=300, connect=30, sock_read=120)
            ) as response:
                print(f"🤖 Connected, starting stream (HTTP {response.status})")
                response.raise_for_status()
                
                full_response = ""
                current_response = ""  # Only the current message content
                chunk_count = 0
                thinking_sent = False
                
                # For action command detection and execution
                accumulated_text = ""  # Accumulate text to detect action commands
                executed_commands = set()  # Track executed commands to avoid duplicates
                action_command_parser = None
                
                # Initialize action command parser if auto_execute_commands is enabled
                if auto_execute_commands and websocket:
                    try:
                        from .direct_commands_parser import DirectCommandsParser
                        action_command_parser = DirectCommandsParser()
                        print(f"🎭 Action command parser initialized for session {session_id}")
                    except Exception as e:
                        print(f"⚠️ Failed to initialize action command parser: {e}")
                        auto_execute_commands = False
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))

                            # Model thinking flag
                            model_is_thinking = (data.get("thinking", False))
                            if model_is_thinking:
                                print(data.get("thinking", "Model is thinking..."))
                            # Handle thinking state
                            if model_is_thinking and not thinking_sent and callback:
                                # await callback("🤔 Thinking...")
                                thinking_sent = True
                            elif not model_is_thinking and thinking_sent and callback:
                                await callback("\r")  # Clear the thinking message
                                thinking_sent = False

                            chunk = data.get("message", {}).get("content", "")
                            if chunk and not model_is_thinking:  # Only send content when not thinking
                                full_response += chunk  # Keep for logging
                                chunk_count += 1
                                current_response += chunk  # Current response content
                                
                                # Accumulate text for action command detection
                                if auto_execute_commands and action_command_parser:
                                    accumulated_text += chunk
                                    
                                    # Look for action commands in accumulated text
                                    await _detect_and_execute_action_commands(
                                        accumulated_text, 
                                        executed_commands, 
                                        action_command_parser, 
                                        websocket
                                    )
                                
                                # Debug: Print chunks to see what we're receiving
                                if chunk_count <= 5:  # Only log first few chunks
                                    print(f"🤖 Chunk {chunk_count}: '{chunk[:30]}...'")
                                
                                if callback:
                                    await callback(chunk)
                            
                            if data.get("done", False):
                                print(f"🤖 Stream completed: {chunk_count} chunks, {len(full_response)} chars")
                                break
                        except json.JSONDecodeError:
                            continue
                
                return current_response.strip()
    
    except aiohttp.ClientConnectorError as e:
        print(f"❌ Connection error to Ollama service: {e}")
        raise ConnectionError(f"Cannot connect to Ollama service at {base_url}. Please ensure Ollama is running.")
    except aiohttp.ServerTimeoutError as e:
        print(f"❌ Server timeout from Ollama service: {e}")
        raise TimeoutError("Ollama service timed out. Try again or check if the model is loaded.")
    except asyncio.TimeoutError as e:
        print(f"❌ Timeout error from Ollama service during streaming: {e}")
        raise TimeoutError("Ollama service timed out during streaming. The response may be taking longer than expected.")
    except aiohttp.ClientResponseError as e:
        print(f"❌ HTTP error from Ollama service: {e}")
        if e.status == 404:
            raise ValueError("Mistral model not found. Please install it with: ollama pull mistral")
        else:
            raise RuntimeError(f"Ollama service error (HTTP {e.status}): {e.message}")
    except Exception as e:
        print(f"❌ Unexpected error in Ollama streaming: {e}")
        raise RuntimeError(f"Unexpected error communicating with AI service: {str(e)}")


async def _detect_and_execute_action_commands(
    accumulated_text: str, 
    executed_commands: set, 
    action_command_parser, 
    websocket
) -> None:
    """
    Detect and execute #action commands in the accumulated response text.
    
    Args:
        accumulated_text: The text accumulated so far from the stream
        executed_commands: Set of already executed commands to avoid duplicates
        action_command_parser: DirectCommandsParser instance
        websocket: WebSocket connection for command execution
    """
    try:
        # Look for action commands in the text
        # This pattern captures complete action commands by looking for:
        # 1. Commands starting with # (optionally followed by "action ")
        # 2. Specific command patterns with their parameters
        # 3. Commands ending at natural boundaries
        
        # Find simple commands first (help, render, tasks, etc.)
        simple_commands = re.findall(r'#(?:action\s+)?(help|render|tasks|analyze(?:\s+context(?:\s+reset)?)?|clear\s+(?:all|id\s+\w+|group\s+\w+))', 
                                   accumulated_text, re.IGNORECASE)
        
        # Find complex commands with timing (add, flash, fade, etc.)
        complex_pattern = r'#(?:action\s+)?((?:add|flash|fade|strobe|set|preset)\s+[^#\n]*?(?:at|to)\s+[\d.]+[sb]?[^#\n]*?)(?=\s*(?:\n|$|\.|\!|\?|,|\s+#|\s+[A-Z][a-z]))'
        complex_commands = re.findall(complex_pattern, accumulated_text, re.IGNORECASE | re.DOTALL)
        
        # Combine all found commands
        all_command_texts = [f"#{cmd.strip()}" for cmd in simple_commands + complex_commands]
        
        for command_text in all_command_texts:
            # Avoid executing the same command multiple times
            if command_text in executed_commands:
                continue
                
            # Validate that this looks like a real action command
            if _is_valid_action_command(command_text):
                executed_commands.add(command_text)
                
                print(f"🎭 Detected action command in AI response: {command_text}")
                
                # Execute the command asynchronously
                try:
                    success, message, additional_data = await action_command_parser.parse_command(
                        command_text, websocket
                    )
                    
                    if success:
                        print(f"✅ Executed action command: {command_text} -> {message}")
                        
                        # Send notification to client
                        if websocket:
                            await websocket.send_json({
                                "type": "actionCommandExecuted",
                                "command": command_text,
                                "success": True,
                                "message": message,
                                "data": additional_data
                            })
                    else:
                        print(f"❌ Failed to execute action command: {command_text} -> {message}")
                        
                        # Send error notification to client
                        if websocket:
                            await websocket.send_json({
                                "type": "actionCommandExecuted",
                                "command": command_text,
                                "success": False,
                                "message": message
                            })
                            
                except Exception as e:
                    print(f"❌ Error executing action command {command_text}: {e}")
                    
                    if websocket:
                        await websocket.send_json({
                            "type": "actionCommandExecuted",
                            "command": command_text,
                            "success": False,
                            "message": f"Error executing command: {str(e)}"
                        })
                        
    except Exception as e:
        print(f"❌ Error in action command detection: {e}")


def _is_valid_action_command(command_text: str) -> bool:
    """
    Check if a detected command text is likely a valid action command.
    
    Args:
        command_text: The command text to validate
        
    Returns:
        True if it looks like a valid action command, False otherwise
    """
    command_text = command_text.lower().strip()
    
    # Remove the # prefix for checking
    if command_text.startswith('#'):
        command_text = command_text[1:].strip()
    
    # Check for known command patterns
    valid_patterns = [
        r'^help$',
        r'^render$',
        r'^tasks$',
        r'^analyze\s*(context\s*(reset)?)?$',
        r'^clear\s+(all|id\s+\w+|group\s+\w+)',
        r'^add\s+\w+\s+to\s+\w+\s+at\s+[\d.]+[sb]?(\s+(for|duration)\s+[\d.]+[sb]?)?',
        r'^(flash|fade|strobe|set|preset)\s+\w+.*?at\s+[\d.]+[sb]?',
        r'^(flash|fade|strobe)\s+\w+.*?(for|duration)\s+[\d.]+[sb]?',
        r'^(flash|fade|strobe)\s+\w+.*?with\s+intensity\s+[\d.]+',
    ]
    
    for pattern in valid_patterns:
        if re.match(pattern, command_text, re.IGNORECASE):
            return True
    
    return False

