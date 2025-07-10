#!/usr/bin/env python3
"""
Test script for improved AI prompt engineering
Tests the enhanced Mistral prompt for better ACTION command generation
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.ai.ollama_client import generate_system_instructions
from backend.models.app_state import app_state
from backend.models.song_metadata import SongMetadata
from backend.ai.cue_interpreter import CueInterpreter
from backend.services.cue_service import CueManager

def create_test_song():
    """Create a test song with realistic structure for testing prompts."""
    from backend.models.song_metadata import Section
    
    # Create song with required parameter
    song = SongMetadata("Test_Song_for_Prompt_Testing", ignore_existing=True)
    
    # Set properties after creation
    song.title = "Test Song for Prompt Testing"
    song.genre = "electronic"
    song.duration = 180.0
    song.bpm = 128
    
    # Set arrangement using Section objects
    song.arrangement = [
        Section("intro", 0.0, 16.0, "Intro section"),
        Section("verse", 16.0, 48.0, "Verse section"), 
        Section("chorus", 48.0, 80.0, "Chorus section"),
        Section("drop", 80.0, 112.0, "Drop section"),
        Section("breakdown", 112.0, 144.0, "Breakdown section"),
        Section("outro", 144.0, 180.0, "Outro section")
    ]
    
    # Set key moments
    song.key_moments = [
        {"name": "energy_build", "time": 40.0, "description": "Building energy before chorus"},
        {"name": "drop_hit", "time": 80.0, "description": "Main drop with high energy"},
        {"name": "breakdown_start", "time": 112.0, "description": "Energy reduces for breakdown"}
    ]
    
    # Set beats with volume and energy
    song.beats = [
        {"time": i * 0.46875, "volume": 0.3 + 0.4 * ((i % 32) / 32), "energy": 0.3 + 0.4 * ((i % 32) / 32)} 
        for i in range(384)  # 180s at 128 BPM
    ]
    
    # Set chords
    song.chords = [
        {"time": i * 1.875, "chord_basic_nashville": ["Am", "F", "C", "G"][i % 4]}
        for i in range(96)  # Chord changes every 2 beats
    ]
    
    return song

def test_original_prompt():
    """Test the current prompt generation."""
    print("=" * 60)
    print("TESTING ORIGINAL PROMPT")
    print("=" * 60)
    
    # Set up test song
    test_song = create_test_song()
    app_state.current_song = test_song
    
    # Generate original prompt
    original_prompt = generate_system_instructions("test_session")
    
    # Save to file for inspection
    with open("/tmp/original_prompt.md", "w") as f:
        f.write(original_prompt)
    
    print(f"Original prompt length: {len(original_prompt)} characters")
    print("\nKey sections found:")
    
    sections = [
        "ACTION COMMAND GUIDELINES",
        "MANDATORY COMMAND STRUCTURE", 
        "ENHANCED ACTION EXAMPLES",
        "CRITICAL REQUIREMENTS",
        "ACTION COMMAND SUCCESS TIPS"
    ]
    
    for section in sections:
        if section in original_prompt:
            print(f"✓ {section}")
        else:
            print(f"✗ {section}")
    
    print(f"\nPrompt saved to: /tmp/original_prompt.md")

def create_improved_prompt_instructions():
    """Create an improved version of the prompt focused on better ACTION command generation."""
    
    return """

**ENHANCED ACTION COMMAND GENERATION:**

**PRECISION REQUIREMENTS:**
Every ACTION command must be IMMEDIATELY EXECUTABLE without interpretation. The cue interpreter expects:

1. **OPERATION CLARITY**: Use exactly these verbs:
   - "Add" (for new cues)
   - "Remove" (for deletion) 
   - "Change" (for modification)

2. **TIMING PRECISION**: Be extremely specific with timing:
   - Musical sections: "during the drop", "at the chorus", "during the verse", "at the bridge"
   - Exact times: "at 67.3s", "from 30s to 45s"
   - Beat-relative: "for 8 beats", "every 4 beats", "for the next 16 beats"
   - Duration hints: "quick" (1-2s), "medium" (4-8s), "long" (16+ beats)

3. **FIXTURE INTELLIGENCE**: Use smart fallbacks the interpreter understands:
   - Primary names: Use exact fixture IDs when known
   - Logical groups: "all RGB fixtures", "moving heads", "left side lights", "right side lights"
   - Type-based: "parcans", "strobes", "moving lights"
   - Positional: "left and right", "mirrored setup", "front lights", "back lights"

4. **EFFECT SPECIFICATION**: Be concrete about visual results:
   - Preset names: "flash", "strobe", "pulse", "rainbow", "fire", "warm", "cool"
   - Color combinations: "red and blue", "warm white", "multi-colored", "cold colors"
   - Effect types: "chase effect", "pulse effect", "strobe effect", "fade effect"
   - Intensity levels: "bright", "dim", "full intensity", "50% brightness"

**INTELLIGENT COMMAND PATTERNS:**

**For High Energy Moments (drops, peaks):**
- "ACTION: Add bright white strobe effect during the drop using all RGB fixtures"
- "ACTION: Add multi-colored fast chase at the breakdown using parcans"
- "ACTION: Add red flash preset on beat hits for 16 beats using moving heads"

**For Build-ups and Transitions:**
- "ACTION: Add slow blue pulse effect for 8 beats before the chorus using left side lights"
- "ACTION: Add warm to cool color fade during the verse using all fixtures"
- "ACTION: Add rising intensity chase effect for the bridge using right side lights"

**For Ambient/Calm Sections:**
- "ACTION: Add soft warm glow during the breakdown using parcans"
- "ACTION: Add gentle purple fade for the outro using all RGB fixtures"
- "ACTION: Add slow color wash effect during the intro using moving heads"

**COMMAND VALIDATION CHECKLIST:**
Before generating any ACTION command, verify it includes:
☐ Clear operation (Add/Remove/Change)
☐ Specific effect description
☐ Precise timing reference
☐ Fixture specification with fallback logic
☐ Musical context consideration
☐ Executable without ambiguity

**SMART TIMING STRATEGIES:**
- Use song arrangement sections for sustained effects
- Reference key moments for accent effects  
- Consider BPM for beat-synchronized effects
- Match effect duration to musical phrases
- Layer multiple effects for complex moments

**FALLBACK INTELLIGENCE:**
When user requests are vague, use these intelligent defaults:
- No fixture specified → "all RGB fixtures"
- No timing specified → "during the [current/most relevant] section"
- No effect specified → Choose based on energy level and genre
- No duration specified → Use musically appropriate phrase length

**ERROR PREVENTION:**
Avoid these common issues that cause execution failures:
- ✗ Vague fixture references: "the lights", "some fixtures"
- ✗ Ambiguous timing: "soon", "later", "sometime"
- ✗ Unclear effects: "something cool", "nice effect"
- ✗ Missing context: Commands without musical awareness
- ✓ Always provide specific, actionable, musically-intelligent commands

**MUSICAL INTELLIGENCE INTEGRATION:**
Use the provided song analysis to make smart suggestions:
- High energy beats → Strobes, flashes, bright colors
- Low energy beats → Fades, pulses, warm colors  
- Chord changes → Color transitions, effect triggers
- Arrangement sections → Sustained effect boundaries
- Key moments → Accent effects, dramatic changes

Remember: Every ACTION command should be so clear and specific that it could be executed immediately without any additional interpretation or user clarification.
"""

def test_improved_prompt_integration():
    """Test how the improved prompt sections would integrate with the existing prompt."""
    print("=" * 60)
    print("TESTING IMPROVED PROMPT INTEGRATION")
    print("=" * 60)
    
    # Get original prompt
    test_song = create_test_song()
    app_state.current_song = test_song
    original_prompt = generate_system_instructions("test_session")
    
    # Add improved sections
    improved_sections = create_improved_prompt_instructions()
    
    # Create combined prompt by replacing the ACTION sections
    # Find where to insert improved content (after the existing ACTION sections)
    action_end_marker = "Remember: Your job is to make the music VISUALLY EXCITING."
    
    if action_end_marker in original_prompt:
        parts = original_prompt.split(action_end_marker)
        enhanced_prompt = parts[0] + improved_sections + "\n\n" + action_end_marker + parts[1]
    else:
        # Fallback: append to end
        enhanced_prompt = original_prompt + improved_sections
    
    # Save enhanced prompt
    with open("/tmp/enhanced_prompt.md", "w") as f:
        f.write(enhanced_prompt)
    
    print(f"Enhanced prompt length: {len(enhanced_prompt)} characters")
    print(f"Enhancement added: {len(enhanced_prompt) - len(original_prompt)} characters")
    print(f"\nEnhanced prompt saved to: /tmp/enhanced_prompt.md")
    
    # Test with sample commands
    print("\nTesting sample command generation patterns:")
    sample_user_requests = [
        "Add some strobes during the drop",
        "Make the lights pulse with the beat",
        "I want colorful effects for the chorus",
        "Add dramatic lighting for the breakdown"
    ]
    
    for request in sample_user_requests:
        print(f"\nUser request: '{request}'")
        print("Expected improved ACTION format:")
        
        if "strobe" in request.lower() and "drop" in request.lower():
            print("  → ACTION: Add bright white strobe effect during the drop using all RGB fixtures")
        elif "pulse" in request.lower() and "beat" in request.lower():
            print("  → ACTION: Add pulse effect synchronized to beats using parcans")
        elif "colorful" in request.lower() and "chorus" in request.lower():
            print("  → ACTION: Add multi-colored chase effect during the chorus using all RGB fixtures")
        elif "dramatic" in request.lower() and "breakdown" in request.lower():
            print("  → ACTION: Add slow red to blue fade during the breakdown using moving heads")

def test_cue_interpreter_with_enhanced_commands():
    """Test that enhanced ACTION commands work well with the improved cue interpreter."""
    print("=" * 60)
    print("TESTING ENHANCED COMMANDS WITH CUE INTERPRETER")
    print("=" * 60)
    
    # Set up test environment
    test_song = create_test_song()
    app_state.current_song = test_song
    
    # Initialize cue interpreter
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    
    # Test enhanced ACTION commands
    enhanced_commands = [
        "Add bright white strobe effect during the drop using all RGB fixtures",
        "Add multi-colored chase effect for 8 beats at the chorus using parcans", 
        "Add slow blue pulse effect during the breakdown using left side lights",
        "Add red flash preset on beat hits for 16 beats using moving heads",
        "Add warm to cool color fade during the verse using right side lights"
    ]
    
    print("Testing enhanced ACTION commands:")
    
    from backend.ai.ollama_client import load_fixture_config
    fixtures, presets, chasers = load_fixture_config()
    
    for i, command in enumerate(enhanced_commands, 1):
        print(f"\n{i}. Testing: '{command}'")
        
        try:
            success, message = interpreter.execute_command(
                command,
                test_song,
                fixtures,
                presets
            )
            
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"   {status}: {message}")
            
        except Exception as e:
            print(f"   ✗ ERROR: {str(e)}")

def test_command_specificity():
    """Test that enhanced commands are more specific and actionable than typical AI outputs."""
    print("=" * 60)
    print("TESTING COMMAND SPECIFICITY IMPROVEMENTS")
    print("=" * 60)
    
    # Compare vague vs enhanced commands
    comparisons = [
        {
            "vague": "Add some cool lights",
            "enhanced": "Add bright white strobe effect during the drop using all RGB fixtures",
            "improvements": ["Specific effect type", "Precise timing", "Clear fixture selection"]
        },
        {
            "vague": "Make it colorful during the good part", 
            "enhanced": "Add multi-colored chase effect during the chorus using parcans",
            "improvements": ["Defined color approach", "Musical section reference", "Fixture type specified"]
        },
        {
            "vague": "Add some movement when it gets quiet",
            "enhanced": "Add slow blue pulse effect during the breakdown using left side lights", 
            "improvements": ["Specific movement type", "Color specification", "Positional targeting"]
        }
    ]
    
    for i, comp in enumerate(comparisons, 1):
        print(f"\n{i}. Specificity Comparison:")
        print(f"   Vague: '{comp['vague']}'")
        print(f"   Enhanced: '{comp['enhanced']}'")
        print(f"   Improvements: {', '.join(comp['improvements'])}")

def main():
    """Run all prompt improvement tests."""
    print("AI LIGHT SHOW - IMPROVED PROMPT TESTING")
    print("=" * 60)
    
    # Test original prompt
    test_original_prompt()
    
    print("\n")
    
    # Test improved prompt integration
    test_improved_prompt_integration()
    
    print("\n")
    
    # Test enhanced commands with interpreter
    test_cue_interpreter_with_enhanced_commands()
    
    print("\n")
    
    # Test command specificity
    test_command_specificity()
    
    print("\n" + "=" * 60)
    print("PROMPT IMPROVEMENT TESTING COMPLETE")
    print("=" * 60)
    print("\nFiles generated:")
    print("- /tmp/original_prompt.md - Current prompt")
    print("- /tmp/enhanced_prompt.md - Improved prompt") 
    print("\nNext steps:")
    print("1. Review generated prompts")
    print("2. Test with live Mistral model")
    print("3. Integrate improvements into ollama_client.py")

if __name__ == "__main__":
    main()
