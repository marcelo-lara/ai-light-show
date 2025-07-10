"""Health checking and status utilities for Ollama service."""

import aiohttp
import asyncio
from typing import Dict, Any, Tuple


async def check_ollama_health(base_url: str = "http://backend-llm:11434") -> Tuple[bool, str]:
    """Check if the Ollama service is available and the mistral model is ready."""
    try:
        async with aiohttp.ClientSession() as session:
            # First check if Ollama is running
            async with session.get(f"{base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    return False, f"Ollama service not responding (HTTP {response.status})"
                
                data = await response.json()
                models = data.get('models', [])
                
                # Check if mistral model is available
                mistral_available = any(model.get('name', '').startswith('mistral') for model in models)
                
                if not mistral_available:
                    available_models = [model.get('name', 'unknown') for model in models]
                    return False, f"Mistral model not found. Available models: {', '.join(available_models) if available_models else 'none'}"
                
                return True, "Ollama service is healthy and mistral model is available"
                
    except aiohttp.ClientConnectorError:
        return False, f"Cannot connect to Ollama service at {base_url}. Please ensure it's running."
    except asyncio.TimeoutError:
        return False, "Ollama service connection timed out"
    except Exception as e:
        return False, f"Unexpected error checking Ollama health: {str(e)}"


def get_ollama_status() -> Dict[str, Any]:
    """Get the current status of the Ollama service synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we can't run this synchronously
            return {"available": False, "message": "Status check requires async context"}
        else:
            is_healthy, message = loop.run_until_complete(check_ollama_health())
            return {"available": is_healthy, "message": message}
    except Exception as e:
        return {"available": False, "message": f"Error checking status: {str(e)}"}
