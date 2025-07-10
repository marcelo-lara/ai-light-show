"""Core communication functions for Ollama API."""

import requests
import json
import aiohttp
import asyncio
from typing import Optional
from .ollama_conversation import get_system_message, update_conversation_history


async def query_ollama_mistral_streaming(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434", callback=None):
    """Send a prompt to ollama/mistral and call callback for each chunk."""
    
    try:
        print(f"🤖 Starting Ollama streaming request for session {session_id}")
        
        # Get existing conversation history for this session
        from .ollama_conversation import get_conversation_messages
        
        messages = get_conversation_messages(session_id)
        
        # Add system message if this is a new conversation
        if not messages:
            messages.append(get_system_message(session_id))
        
        # Add the new user message
        messages.append({"role": "user", "content": prompt})
        
        print(f"🤖 Conversation has {len(messages)} messages, prompt length: {len(prompt)} chars")
        
        request_data = {
            "model": "mistral", 
            "messages": messages,
            "stream": True
        }
        
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
                chunk_count = 0
                
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line.decode('utf-8'))
                            chunk = data.get("message", {}).get("content", "")
                            if chunk:
                                full_response += chunk
                                chunk_count += 1
                                if callback:
                                    await callback(chunk)
                            
                            if data.get("done", False):
                                print(f"🤖 Stream completed: {chunk_count} chunks, {len(full_response)} chars")
                                break
                        except json.JSONDecodeError:
                            continue
                
                # Add the assistant's response to conversation history
                if full_response:
                    update_conversation_history(session_id, messages, full_response)
                    print(f"🤖 Response saved to conversation history")
    
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


def query_ollama_mistral(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434"):
    """Send a prompt to the ollama/mistral model and return the response text with conversation history."""
    
    # Get existing conversation history for this session
    from .ollama_conversation import get_conversation_messages, update_conversation_history
    
    messages = get_conversation_messages(session_id)
    
    # Add system message if this is a new conversation
    if not messages:
        messages.append(get_system_message(session_id))
    
    # Add the new user message
    messages.append({"role": "user", "content": prompt})
    
    request_data = {
        "model": "mistral",
        "messages": messages,
        "stream": True  # Enable streaming
    }
    
    response = requests.post(
        f"{base_url}/api/chat",
        json=request_data,
        timeout=300,  # Increased from 60 to 300 seconds
        stream=True
    )
    response.raise_for_status()
    
    full_response = ""
    
    # Process streaming response
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    full_response += chunk
                
                # Check if done
                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                continue
    
    # Add the assistant's response to conversation history
    if full_response:
        update_conversation_history(session_id, messages, full_response)
    
    return full_response


async def query_ollama_with_actions(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434"):
    """Enhanced query function that processes AI actions for user confirmation."""
    
    # Get AI response
    ai_response = query_ollama_mistral(prompt, session_id, base_url)
    
    # Extract action proposals (removes ACTION: lines from response)
    from .ollama_actions import extract_action_proposals
    cleaned_response, action_proposals = extract_action_proposals(ai_response, session_id)
    
    return cleaned_response, action_proposals
