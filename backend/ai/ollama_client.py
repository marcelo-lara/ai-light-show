import requests
import json
import aiohttp
import os
from pathlib import Path
from datetime import datetime
from backend.config import AI_CACHE, MASTER_FIXTURE_CONFIG, FIXTURE_PRESETS, CHASER_TEMPLATE_PATH

# Store conversation history per user/session (instead of deprecated context)
_conversation_histories = {}

def load_fixture_config():
    """Load the current fixture configuration, presets, and chaser templates."""
    
    try:
        # Load master fixture config
        with open(MASTER_FIXTURE_CONFIG, 'r') as f:
            fixtures = json.load(f)
        
        # Load fixture presets
        with open(FIXTURE_PRESETS, 'r') as f:
            presets = json.load(f)
        
        # Load chaser templates
        with open(CHASER_TEMPLATE_PATH, 'r') as f:
            chasers = json.load(f)
        
        return fixtures, presets, chasers
    except Exception as e:
        print(f"Warning: Could not load fixture configuration: {e}")
        return [], [], []

def generate_system_instructions():
    """Generate dynamic system instructions based on current fixture configuration."""
    fixtures, presets, chasers = load_fixture_config()
    
    # Build fixture summary
    fixture_summary = []
    for fixture in fixtures:
        fixture_info = f"- **{fixture['name']}** (ID: {fixture['id']}, Type: {fixture['type']})"
        if 'channels' in fixture:
            channels = list(fixture['channels'].keys())
            fixture_info += f" - Channels: {', '.join(channels[:5])}" # Limit for readability
            if len(channels) > 5:
                fixture_info += f" (+{len(channels)-5} more)"
        fixture_summary.append(fixture_info)
    
    # Build preset summary
    preset_summary = []
    for preset in presets[:10]:  # Limit for readability
        preset_summary.append(f"- **{preset['name']}**: {preset.get('description', 'No description')}")
    
    # Build chaser summary
    chaser_summary = []
    for chaser in chasers[:10]:  # Limit for readability
        fixture_ids = chaser.get('fixture_ids', [])
        chaser_summary.append(f"- **{chaser['name']}**: {chaser.get('description', 'No description')} (Fixtures: {', '.join(fixture_ids)})")
    
    base_instructions = """You are a creative light show designer AI that helps create stunning visual experiences synchronized to music. Your role is to help users:

1. **Design light shows** - Create dynamic sequences, effects, and synchronized performances
2. **Music synchronization** - Match lighting to beats, drops, vocals, and musical elements
3. **Creative effects** - Suggest color palettes, movement patterns, and visual themes
4. **Performance optimization** - Enhance visual impact and audience engagement

**RESPONSE STYLE:**
- For greetings (hi, hello, hey): Respond with just "Hey! Ready to create some light magic? What's the vibe?"
- For general questions: Keep responses under 3 sentences
- For specific requests: Give direct, actionable advice
- Don't repeat or explain your role unless specifically asked

**CREATIVE GUIDELINES:**
- Focus on visual storytelling and artistic expression through lighting
- Suggest specific color combinations, timing patterns, and effect sequences
- Match lighting moods to musical genres and energy levels
- Be SHORT and CONCISE - give actionable creative direction
- Always use the actual fixtures, presets, and chasers available below
- Think like a lighting designer, not a technician

**OFF-TOPIC HANDLING:**
If users ask about unrelated topics, respond with:
"That's not in my wheelhouse - I'm more about making lights dance than [topic]. Let's focus on the box! What lighting question can I help with?"

**YOUR LIGHTING PALETTE:**

**Available Fixtures:**
"""
    
    if fixture_summary:
        base_instructions += "\n".join(fixture_summary)
    else:
        base_instructions += "No fixtures currently configured."
    
    base_instructions += "\n\n**Available Presets:**\n"
    if preset_summary:
        base_instructions += "\n".join(preset_summary)
        if len(presets) > 10:
            base_instructions += f"\n... and {len(presets)-10} more presets available"
    else:
        base_instructions += "No presets currently configured."
    
    base_instructions += "\n\n**Available Chaser Templates:**\n"
    if chaser_summary:
        base_instructions += "\n".join(chaser_summary)
        if len(chasers) > 10:
            base_instructions += f"\n... and {len(chasers)-10} more chaser templates available"
    else:
        base_instructions += "No chaser templates currently configured."
    
    base_instructions += """

**SYSTEM READY:**
- All fixtures are connected and responsive
- Audio analysis provides beat detection and spectral data
- Real-time synchronization is active
- Ready to create shows immediately

**DESIGN APPROACH:**
- **For energetic music**: Use fast chasers, bright colors, strobes
- **For ambient music**: Smooth transitions, warm colors, slow movements  
- **For drops/builds**: Build intensity with color temperature and speed
- **For vocals**: Highlight with specific fixtures or color changes

**IMPORTANT:** Only suggest effects using the fixtures, presets, and chasers listed above. Assume everything is working - focus purely on creative light show design and musical synchronization.
"""
    
    # Save the generated instructions to debug file
    _save_system_instructions(base_instructions)
    
    return base_instructions

def get_system_message():
    """Get the system message for conversations with current fixture configuration."""
    return {"role": "system", "content": generate_system_instructions()}

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

def refresh_system_configuration():
    """Refresh system configuration by reloading fixture data and clearing conversations."""
    # Clear all conversations to apply new configuration
    _conversation_histories.clear()

def get_current_fixtures():
    """Get current fixture configuration for external use."""
    fixtures, _, _ = load_fixture_config()
    return fixtures

def get_current_presets():
    """Get current presets for external use."""
    _, presets, _ = load_fixture_config()
    return presets

def get_current_chasers():
    """Get current chaser templates for external use."""
    _, _, chasers = load_fixture_config()
    return chasers

def _save_system_instructions(instructions: str):
    """Save the current system instructions to a debug file."""
    debug_dir = AI_CACHE / "ollama_debug"
    debug_dir.mkdir(exist_ok=True)
    
    instructions_file = debug_dir / "system_instructions.md"
    
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(instructions_file, 'w') as f:
            f.write(f"# System Instructions Generated\n")
            f.write(f"**Generated at:** {current_time}\n\n")
            f.write("---\n\n")
            f.write(instructions)
            f.write(f"\n\n---\n*Last updated: {current_time}*\n")
    except Exception as e:
        print(f"Warning: Could not save system instructions: {e}")

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