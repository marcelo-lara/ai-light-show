"""System instruction generation for Ollama AI conversations."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from backend.config import AI_CACHE, MASTER_FIXTURE_CONFIG, FIXTURE_PRESETS, CHASER_TEMPLATE_PATH
from backend.models.app_state import app_state


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


def generate_system_instructions(session_id: str = "default"):
    """Generate dynamic system instructions based on current fixture configuration and song context."""
    fixtures, presets, chasers = load_fixture_config()
    
    # Get current song from AppState
    current_song = app_state.current_song
    
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
- For general questions: Keep responses under 3 sentences and END with specific ACTION suggestions
- For specific requests: Give direct, actionable advice with precise ACTION commands
- Don't repeat or explain your role unless specifically asked
- ALWAYS end lighting discussions with concrete ACTION commands the user can execute
- Be creative but practical - suggest effects that will actually look good
- Focus on ACTIONABLE specificity - every response should move toward executable lighting commands

**CREATIVE GUIDELINES:**
- Focus on visual storytelling and artistic expression through lighting
- Suggest specific color combinations, timing patterns, and effect sequences
- Match lighting moods to musical genres and energy levels
- Be SHORT and CONCISE - give actionable creative direction
- Always use the actual fixtures, presets, and chasers available below
- Think like a lighting designer, not a technician
- PRIORITIZE SPECIFICITY: Always include exact timing, fixture names, and effect details

**COMMUNICATION PRINCIPLES:**
- When users describe what they want, IMMEDIATELY translate it into specific, executable ACTION commands
- Use musical analysis data to suggest precise timing for effects
- Reference actual fixture names and preset names from the configuration
- Consider the genre and energy level when suggesting colors and effects
- Default to using multiple fixtures for bigger impact unless specifically asked otherwise
- Provide 2-3 ACTION options when possible to give users choices

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
    
    # Add current song information if available
    if current_song:
        base_instructions += _generate_song_context(current_song)
    else:
        base_instructions += """

**CURRENT SONG:**
- No song currently loaded
- Ready to receive song information for synchronized lighting"""

    base_instructions += _get_action_command_guidelines()
    
    # Save the generated instructions to debug file
    _save_system_instructions(base_instructions)
    
    return base_instructions


def _generate_song_context(current_song):
    """Generate the song-specific context for system instructions."""
    # Format arrangement sections for display
    arrangement_info = "No arrangement sections"
    if hasattr(current_song, 'arrangement') and current_song.arrangement:
        sections = []
        for section in current_song.arrangement[:5]:  # Limit for readability
            if hasattr(section, 'name') and hasattr(section, 'start') and hasattr(section, 'end'):
                sections.append(f"{section.name} ({section.start:.1f}s-{section.end:.1f}s)")
            elif isinstance(section, dict):
                sections.append(f"{section.get('name', 'Unknown')} ({section.get('start', 0):.1f}s-{section.get('end', 0):.1f}s)")
        if sections:
            arrangement_info = ", ".join(sections)
            if len(current_song.arrangement) > 5:
                arrangement_info += f" (+{len(current_song.arrangement)-5} more sections)"

    # Format key moments
    key_moments_info = "None detected"
    if hasattr(current_song, 'key_moments') and current_song.key_moments:
        moments = []
        for moment in current_song.key_moments[:8]:  # Limit for readability
            if isinstance(moment, dict):
                time_str = f"{moment.get('time', 0):.1f}s"
                name = moment.get('name', 'Unknown')
                desc = moment.get('description', '')
                moments.append(f"{name} ({time_str}): {desc}")
        if moments:
            key_moments_info = " | ".join(moments)
            if len(current_song.key_moments) > 8:
                key_moments_info += f" (+{len(current_song.key_moments)-8} more)"

    # Format beat analysis
    beat_analysis = "No beat data"
    energy_levels = []
    if hasattr(current_song, 'beats') and current_song.beats:
        total_beats = len(current_song.beats)
        
        # Calculate energy and volume statistics
        volume_levels = []
        beat_times = []
        
        for beat in current_song.beats:
            if isinstance(beat, dict):
                if 'energy' in beat:
                    energy_levels.append(beat['energy'])
                if 'volume' in beat:
                    volume_levels.append(beat['volume'])
                if 'time' in beat:
                    beat_times.append(beat['time'])
        
        beat_analysis = f"{total_beats} beats detected"
        
        # Add energy analysis
        if energy_levels:
            avg_energy = sum(energy_levels) / len(energy_levels)
            max_energy = max(energy_levels)
            
            # Find peak energy moments for highlighting
            peak_threshold = avg_energy + (max_energy - avg_energy) * 0.7
            peak_moments = []
            for i, (beat, energy) in enumerate(zip(current_song.beats, energy_levels)):
                if energy >= peak_threshold and isinstance(beat, dict) and 'time' in beat:
                    peak_moments.append(f"{beat['time']:.1f}s")
            
            beat_analysis += f" | Energy: avg={avg_energy:.2f}, peak={max_energy:.2f}"
            if peak_moments:
                beat_analysis += f" | High energy at: {', '.join(peak_moments[:5])}"
                if len(peak_moments) > 5:
                    beat_analysis += f" (+{len(peak_moments)-5} more)"

    # Generate intelligent lighting suggestions
    lighting_suggestions = ""
    if energy_levels:
        avg_energy = sum(energy_levels) / len(energy_levels)
        max_energy = max(energy_levels)
        high_energy_threshold = avg_energy + (max_energy - avg_energy) * 0.7
        
        # Genre-specific advice
        genre_advice = {
            'electronic': 'Sync strobes to synthetic beats, use cool colors (blue/cyan), fast chases',
            'rock': 'Strong beat emphasis, warm colors (red/orange), dramatic lighting changes',
            'ambient': 'Slow transitions, soft colors, minimal movement, atmospheric effects',
            'pop': 'Bright colors, synchronized to vocals, crowd-pleasing effects',
            'techno': 'Repetitive patterns, industrial colors, precise beat sync',
            'unknown': 'Adapt lighting to detected energy levels and musical structure'
        }
        
        current_genre_advice = genre_advice.get(current_song.genre.lower(), genre_advice['unknown'])
        key_moment_count = len([m for m in current_song.key_moments if isinstance(m, dict)]) if hasattr(current_song, 'key_moments') and current_song.key_moments else 0
        
        lighting_suggestions = f"""

**INTELLIGENT LIGHTING SUGGESTIONS:**
Based on the current song analysis, here are contextual recommendations:
- **For high-energy moments** (energy > {high_energy_threshold:.2f}): Use fast strobes, bright colors, quick chases
- **For build-ups**: Gradually increase intensity, use rising patterns, warm to cool color transitions  
- **For breakdowns**: Minimal lighting, single colors, slow movements
- **For {current_song.genre} genre**: {current_genre_advice}
- **Sync Strategy**: Match major lighting changes to the {key_moment_count} key moments identified
- **Timing Precision**: Use {60/current_song.bpm*1000:.0f}ms per beat intervals for perfect sync"""

    return f"""

**CURRENT SONG:**
- **Title**: {current_song.title}
- **Genre**: {current_song.genre}
- **BPM**: {current_song.bpm}
- **Duration**: {current_song.duration:.1f}s

**MUSICAL STRUCTURE:**
- **Arrangement**: {arrangement_info}
- **Key Moments**: {key_moments_info}

**RHYTHMIC ANALYSIS:**
- **Beat Analysis**: {beat_analysis}{lighting_suggestions}"""


def _get_action_command_guidelines():
    """Get the comprehensive ACTION command guidelines."""
    return """

**ACTION COMMAND GUIDELINES:**
When creating ACTION commands, be SPECIFIC and UNAMBIGUOUS. Every ACTION must include ALL required elements:

**MANDATORY COMMAND STRUCTURE:**
Each ACTION must specify: [OPERATION] [EFFECT] [TIMING] [FIXTURES]

**Operation Types:**
- "Add" - Create new lighting cue
- "Remove" - Delete existing cues
- "Change" - Modify existing cues

**Timing Specifications (REQUIRED):**
- Exact times: "at 45.2s", "from 30s to 60s"
- Musical sections: "during the drop", "at the chorus", "during the bridge", "in the breakdown", "during the verse", "at the intro"
- Relative timing: "for the next 4 beats", "for 8 seconds", "until the next section"
- Beat-based: "on beat 32", "every 4 beats", "for 16 beats"

**Fixture Specifications (REQUIRED):**
- Exact names: "ParCan L", "ParCan R", "Head EL-150", "Proton L", "Proton R"
- Logical groups: "all parcans", "both parcans", "moving heads", "both protons"
- Positional groups: "left side lights", "right side lights", "all RGB fixtures"
- When unsure, default to "all RGB fixtures"

**Effect Specifications (REQUIRED):**
- Preset names: "flash", "pulse", "strobe", "rainbow", "fire", "warm", "cool"
- Custom colors: "bright red", "deep blue", "warm white", "green and blue", "purple and orange"
- Intensity: "full brightness", "50% intensity", "dim", "bright"
- Speed/Duration: "quick flash", "slow fade", "2-second pulse", "fast strobe", "instant"

**ENHANCED ACTION EXAMPLES:**
- "ACTION: Add bright white flash preset at 67.3s using both parcans"
- "ACTION: Add red and blue pulse effect during the drop using all RGB fixtures"
- "ACTION: Add fast white strobe for 8 beats during the breakdown using Head EL-150"
- "ACTION: Add warm orange glow from 90s to 120s using left side lights"
- "ACTION: Remove all lighting cues between 45s and 60s"
- "ACTION: Add rainbow chase effect during the chorus using all fixtures"
- "ACTION: Add green flash on beat hits during the verse using both protons"
- "ACTION: Add slow blue fade for 16 beats at the bridge using moving heads"

**CRITICAL REQUIREMENTS - EVERY ACTION MUST:**
1. Start with "ACTION:" followed by a single, complete command
2. Include an operation verb (Add/Remove/Change)
3. Specify the exact effect/preset OR custom colors and intensity
4. Include precise timing (time, section, or duration)
5. Name specific fixtures OR use logical groups like "all RGB fixtures"
6. Use fixture names and preset names from the available configuration
7. Be executable as a single lighting command
8. Consider the musical context and energy level for appropriate effects

Remember: Your job is to make the music VISUALLY EXCITING. Every response should move the user closer to having an amazing light show!
"""


def get_system_message(session_id: str = "default"):
    """Get the system message for conversations with current fixture configuration and song context."""
    return {"role": "system", "content": generate_system_instructions(session_id)}


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
