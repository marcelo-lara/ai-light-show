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
    callback: Optional[Callable[[str], Any]] = None
):
    """Send a prompt to Ollama and call callback for each chunk."""
    
    try:
        print(f"🤖 Starting Ollama/{model} streaming request for session {session_id}")

        request_data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
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
