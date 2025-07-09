import requests
import json
import aiohttp

# Store conversation history per user/session (instead of deprecated context)
_conversation_histories = {}

def query_ollama_mistral(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434"):
    """Send a prompt to the ollama/mistral model and return the response text with conversation history."""
    
    # Get existing conversation history for this session
    messages = _conversation_histories.get(session_id, [])
    
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
        timeout=60,
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
        messages.append({"role": "assistant", "content": full_response})
        _conversation_histories[session_id] = messages
    
    return full_response

async def query_ollama_mistral_streaming(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434", callback=None):
    """Send a prompt to ollama/mistral and call callback for each chunk."""
    # Get existing conversation history for this session
    messages = _conversation_histories.get(session_id, [])
    
    # Add the new user message
    messages.append({"role": "user", "content": prompt})
    
    request_data = {
        "model": "mistral",
        "messages": messages,
        "stream": True
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/api/chat",
            json=request_data,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            response.raise_for_status()
            
            full_response = ""
            
            async for line in response.content:
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        chunk = data.get("message", {}).get("content", "")
                        if chunk:
                            full_response += chunk
                            if callback:
                                await callback(chunk)
                        
                        if data.get("done", False):
                            break
                    except json.JSONDecodeError:
                        continue
            
            # Add the assistant's response to conversation history
            if full_response:
                messages.append({"role": "assistant", "content": full_response})
                _conversation_histories[session_id] = messages

def clear_conversation(session_id: str = "default"):
    """Clear conversation history for a session."""
    if session_id in _conversation_histories:
        del _conversation_histories[session_id]

def get_active_sessions():
    """Get list of active conversation sessions."""
    return list(_conversation_histories.keys())

#
# Response from Ollama: {'model': 'mistral', 'created_at': '2025-07-09T01:40:50.111488497Z', 'response': " Hello! How can I help you today?\n\nIf you have any questions or need assistance with something, feel free to ask. I'm here to help! If you just want to chat or share some thoughts, we can do that too. Let me know what you'd like to talk about. :)", 'done': True, 'done_reason': 'stop', 'context': [3, 29473, 12782, 4, 29473, 23325, 29576, 2370, 1309, 1083, 2084, 1136, 3922, 29572, 781, 781, 4149, 1136, 1274, 1475, 4992, 1210, 1695, 12379, 1163, 2313, 29493, 2369, 2701, 1066, 2228, 29491, 1083, 29510, 29487, 2004, 1066, 2084, 29576, 1815, 1136, 1544, 1715, 1066, 11474, 1210, 4866, 1509, 8171, 29493, 1246, 1309, 1279, 1137, 2136, 29491, 3937, 1296, 1641, 1535, 1136, 29510, 29483, 1505, 1066, 2753, 1452, 29491, 15876], 'total_duration': 5738611868, 'load_duration': 1137774303, 'prompt_eval_count': 5, 'prompt_eval_duration': 156982143, 'eval_count': 65, 'eval_duration': 4443280613}