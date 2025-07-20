"""Simplified streaming functionality for Ollama API."""

import aiohttp
import asyncio
import json
from typing import Optional, Callable, Any

async def query_ollama_streaming(
    prompt: str, 
    session_id: str = "default", 
    model: str = "mixtral",
    base_url: str = "http://llm-service:11434", 
    callback: Optional[Callable[[str], Any]] = None,
    context: Optional[str] = None,
    conversation_history: Optional[list] = None,
    temperature: float = 0.7
) -> str:
    """Send a prompt to Ollama and call callback for each chunk."""
    
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
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))

                            # Model thinking flag
                            model_is_thinking = (data.get("thinking", False))
                            
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

