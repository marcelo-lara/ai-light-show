import requests
import json

# Store conversation context per user/session
_conversation_contexts = {}

def query_ollama_mistral(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434"):
    """Send a prompt to the ollama/mistral model and return the response text with context."""
    
    # Get existing context for this session
    context = _conversation_contexts.get(session_id)
    
    request_data = {
        "model": "mistral",
        "prompt": prompt,
        "stream": True  # Enable streaming
    }
    
    # Include context if we have it
    if context:
        request_data["context"] = context
    
    response = requests.post(
        f"{base_url}/api/generate",
        json=request_data,
        timeout=60,
        stream=True
    )
    response.raise_for_status()
    
    full_response = ""
    final_context = None
    
    # Process streaming response
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line)
                chunk = data.get("response", "")
                if chunk:
                    full_response += chunk
                
                # Store context when done
                if data.get("done", False):
                    final_context = data.get("context")
                    break
            except json.JSONDecodeError:
                continue
    
    # Store the new context for future messages
    if final_context:
        _conversation_contexts[session_id] = final_context
    
    return full_response

async def query_ollama_mistral_streaming(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434", callback=None):
    """Send a prompt to ollama/mistral and call callback for each chunk."""
    context = _conversation_contexts.get(session_id)
    
    request_data = {
        "model": "mistral",
        "prompt": prompt,
        "stream": True
    }
    
    if context:
        request_data["context"] = context
    
    response = requests.post(
        f"{base_url}/api/generate",
        json=request_data,
        timeout=60,
        stream=True
    )
    response.raise_for_status()
    
    final_context = None
    
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line)
                chunk = data.get("response", "")
                if chunk and callback:
                    await callback(chunk)
                
                if data.get("done", False):
                    final_context = data.get("context")
                    break
            except json.JSONDecodeError:
                continue
    
    if final_context:
        _conversation_contexts[session_id] = final_context

def clear_conversation(session_id: str = "default"):
    """Clear conversation context for a session."""
    if session_id in _conversation_contexts:
        del _conversation_contexts[session_id]

def get_active_sessions():
    """Get list of active conversation sessions."""
    return list(_conversation_contexts.keys())

#
# Response from Ollama: {'model': 'mistral', 'created_at': '2025-07-09T01:40:50.111488497Z', 'response': " Hello! How can I help you today?\n\nIf you have any questions or need assistance with something, feel free to ask. I'm here to help! If you just want to chat or share some thoughts, we can do that too. Let me know what you'd like to talk about. :)", 'done': True, 'done_reason': 'stop', 'context': [3, 29473, 12782, 4, 29473, 23325, 29576, 2370, 1309, 1083, 2084, 1136, 3922, 29572, 781, 781, 4149, 1136, 1274, 1475, 4992, 1210, 1695, 12379, 1163, 2313, 29493, 2369, 2701, 1066, 2228, 29491, 1083, 29510, 29487, 2004, 1066, 2084, 29576, 1815, 1136, 1544, 1715, 1066, 11474, 1210, 4866, 1509, 8171, 29493, 1246, 1309, 1279, 1137, 2136, 29491, 3937, 1296, 1641, 1535, 1136, 29510, 29483, 1505, 1066, 2753, 1452, 29491, 15876], 'total_duration': 5738611868, 'load_duration': 1137774303, 'prompt_eval_count': 5, 'prompt_eval_duration': 156982143, 'eval_count': 65, 'eval_duration': 4443280613}