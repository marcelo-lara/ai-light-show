import requests
import json
import aiohttp

# Store conversation history per user/session (instead of deprecated context)
_conversation_histories = {}

# System instructions for the AI light show assistant
SYSTEM_INSTRUCTIONS = """You are an AI assistant for a light show system that controls DMX lighting fixtures synchronized to music. Your role is to help users:

1. **Configure lighting fixtures** - Help set up DMX channels, fixture types, and positioning
2. **Create light shows** - Assist with programming chasers, effects, and synchronized sequences
3. **Music analysis** - Help with beat detection, tempo analysis, and audio-reactive programming
4. **Troubleshoot issues** - Debug DMX communication, fixture problems, and timing issues
5. **Optimize performances** - Suggest improvements for visual impact and synchronization

**IMPORTANT GUIDELINES:**
- Stay focused on lighting, DMX, music synchronization, and related technical topics
- If users ask about unrelated topics, politely redirect them back to light show assistance
- Provide specific, actionable advice for lighting control and programming
- Ask clarifying questions about their setup (fixture types, DMX addresses, software, etc.)
- Be concise but thorough in your technical explanations

**OFF-TOPIC HANDLING:**
If the user asks about topics unrelated to lighting/music/DMX, respond with:
"I'm specifically designed to help with light shows, DMX lighting, and music synchronization. Let's focus on that! What lighting or music-related question can I help you with?"

**CURRENT CONTEXT:** You're working with a system that includes:
- DMX fixture control via Art-Net
- Audio analysis with beat detection and spectral analysis  
- Real-time light show rendering and timeline engines
- Web-based control interface
- Support for various fixture types (RGB, moving heads, strobes, etc.)
"""

def get_system_message():
    """Get the system message for conversations."""
    return {"role": "system", "content": SYSTEM_INSTRUCTIONS}

def query_ollama_mistral(prompt: str, session_id: str = "default", base_url: str = "http://backend-llm:11434"):
    """Send a prompt to the ollama/mistral model and return the response text with conversation history."""
    
    # Get existing conversation history for this session
    messages = _conversation_histories.get(session_id, [])
    
    # Add system message if this is a new conversation
    if not messages:
        messages.append(get_system_message())
    
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
    
    # Add system message if this is a new conversation
    if not messages:
        messages.append(get_system_message())
    
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

def get_conversation_history(session_id: str = "default"):
    """Get the conversation history for a session."""
    return _conversation_histories.get(session_id, [])

def reset_conversation_with_system(session_id: str = "default"):
    """Reset conversation and start fresh with system message."""
    _conversation_histories[session_id] = [get_system_message()]

def update_system_instructions(new_instructions: str):
    """Update the system instructions and reset all conversations."""
    global SYSTEM_INSTRUCTIONS
    SYSTEM_INSTRUCTIONS = new_instructions
    # Clear all conversations to apply new instructions
    _conversation_histories.clear()

#
# Example response from modern Ollama /api/chat endpoint:
# {
#   'model': 'mistral',
#   'created_at': '2025-07-09T15:26:02.111Z',
#   'message': {
#     'role': 'assistant',
#     'content': 'Hello! I can help you with DMX lighting, fixture setup, and music synchronization...'
#   },
#   'done': True,
#   'done_reason': 'stop',
#   'total_duration': 5738611868,
#   'load_duration': 1137774303,
#   'prompt_eval_count': 15,
#   'prompt_eval_duration': 156982143,
#   'eval_count': 65,
#   'eval_duration': 4443280613
# }