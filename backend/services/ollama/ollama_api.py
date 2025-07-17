"""Core communication functions for Ollama API."""

import requests
import json


def query_ollama(prompt: str, model: str = "mistral", base_url: str = "http://llm-server:11434") -> str:
    """Send a prompt to the llm-server and return the response text. Model can be specified."""
    request_data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=request_data,
        timeout=300
    )
    response.raise_for_status()

    full_response = ""
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line)
                chunk = data.get("message", {}).get("content", "")
                if chunk:
                    full_response += chunk

                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                continue

    return full_response
