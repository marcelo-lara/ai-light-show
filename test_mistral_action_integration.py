#!/usr/bin/env python3
"""
Test script for Mistral ACTION command integration with CueInterpreter.
This script tests the complete flow from ACTION extraction to cue execution.
"""

import sys
import os
sys.path.insert(0, '/home/darkangel/ai-light-show')

from backend.ai.ollama_actions import extract_action_proposals, execute_confirmed_action
from backend.ai.cue_interpreter import CueInterpreter
from backend.services.cue_service import CueManager
from backend.models.song_metadata import SongMetadata
from backend.models.app_state import app_state

def setup_test_environment():
    """Set up test environment with mock song and fixtures."""
    # Create test song
    test_song = SongMetadata("test_song")
    test_song.duration = 180.0
    test_song.bpm = 128
    test_song.arrangement = []
    test_song.genre = "electronic"
    test_song.title = "Test Track"
    
    # Set current song in app_state
    app_state.current_song = test_song
    
    return test_song

def test_action_extraction():
    """Test ACTION command extraction from AI responses."""
    print("🧪 Testing ACTION command extraction...")
    print("=" * 60)
    
    # Simulate AI responses with various ACTION commands
    test_responses = [
        """I'll create a bright strobe effect for the drop section.

ACTION: Add white flash preset at 45.2s using all RGB fixtures

This will sync perfectly with the beat drop and create maximum visual impact.""",
        
        """Let me add some dynamic lighting for the chorus.

ACTION: Add multi-colored chase effect during the chorus using parcans
ACTION: Add fast strobe for 8 beats at the breakdown using moving heads

These effects will complement the energy buildup in the music.""",
        
        """Here's a complex lighting sequence:

ACTION: Add bright red flash at 30s using left side lights
ACTION: Add blue pulse effect for 16 beats during the bridge using right side lights
ACTION: Remove all lighting cues between 60s and 90s

This creates a dramatic lighting narrative."""
    ]
    
    for i, response in enumerate(test_responses, 1):
        print(f"\n📝 Test {i}: AI Response")
        print("-" * 40)
        print(f"Original response:\n{response[:100]}...")
        
        # Extract ACTION proposals
        cleaned_response, action_proposals = extract_action_proposals(response)
        
        print(f"\n✅ Extracted {len(action_proposals)} ACTION(s):")
        print(f"Cleaned response: {cleaned_response[:100]}...")
        
        for j, proposal in enumerate(action_proposals):
            print(f"\n   Action {j+1}:")
            print(f"     ID: {proposal.get('id')}")
            print(f"     Command: {proposal.get('command')}")
            print(f"     Description: {proposal.get('description')}")
            print(f"     Can Execute: {proposal.get('can_execute')}")
            print(f"     Confidence: {proposal.get('confidence')}")
            if 'error' in proposal:
                print(f"     Error: {proposal.get('error')}")

def test_cue_interpreter_integration():
    """Test CueInterpreter with extracted ACTION commands."""
    print("\n🔗 Testing CueInterpreter integration...")
    print("=" * 60)
    
    # Mock fixtures and presets (from master_fixture_config.json)
    mock_fixtures = [
        {'id': 'parcan_l', 'name': 'ParCan L', 'type': 'rgb'},
        {'id': 'parcan_r', 'name': 'ParCan R', 'type': 'rgb'},
        {'id': 'head_el150', 'name': 'Head EL-150', 'type': 'moving_head'},
        {'id': 'proton_l', 'name': 'Proton L', 'type': 'rgb'},
        {'id': 'proton_r', 'name': 'Proton R', 'type': 'rgb'},
    ]
    
    mock_presets = [
        {'name': 'flash', 'description': 'Flash effect'},
        {'name': 'strobe', 'description': 'Strobe effect'},
        {'name': 'chase', 'description': 'Chase effect'},
        {'name': 'fade', 'description': 'Fade effect'},
        {'name': 'pulse', 'description': 'Pulse effect'},
    ]
    
    test_song = setup_test_environment()
    cue_manager = CueManager()
    interpreter = CueInterpreter(cue_manager)
    
    # Test ACTION commands that Mistral might generate
    test_action_commands = [
        "Add bright white flash preset at 45.2s using all RGB fixtures",
        "Add multi-colored chase effect during the chorus using parcans",
        "Add fast strobe for 8 beats at the breakdown using moving heads",
        "Add red pulse effect for 16 beats during the bridge using right side lights",
        "Remove all lighting cues between 60s and 90s",
        "Add warm white glow from 30s to 60s using left side lights",
        "Add rainbow chase effect during the drop using all fixtures"
    ]
    
    print("Testing individual ACTION commands:")
    
    for i, command in enumerate(test_action_commands, 1):
        print(f"\n📝 Test {i}: {command}")
        print("-" * 40)
        
        try:
            # Test interpretation
            interpretation = interpreter.interpret_command(
                command, test_song, mock_fixtures, mock_presets
            )
            
            print(f"✅ Interpretation successful:")
            print(f"   Operation: {interpretation['operation']}")
            print(f"   Time: {interpretation['time']}")
            print(f"   Fixtures: {interpretation['fixtures']}")
            print(f"   Preset: {interpretation['preset']}")
            print(f"   Confidence: {interpretation['confidence']:.2f}")
            
            # Test execution
            success, message = interpreter.execute_command(
                command, test_song, mock_fixtures, mock_presets
            )
            
            print(f"🎯 Execution: {'✅ SUCCESS' if success else '❌ FAILED'}")
            print(f"   Message: {message}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

def test_full_integration_flow():
    """Test the complete integration flow from ACTION extraction to execution."""
    print("\n🎯 Testing complete integration flow...")
    print("=" * 60)
    
    test_song = setup_test_environment()
    
    # Simulate a complete AI response with ACTION commands
    ai_response = """I'll create an exciting lighting sequence for your track!

For the intro, I'll start with a subtle warm glow, then build up to intense strobes for the drop.

ACTION: Add warm white glow from 10s to 30s using all RGB fixtures
ACTION: Add fast white strobe for 8 beats at 45s using parcans
ACTION: Add multi-colored chase effect during the chorus using moving heads

This will create a dramatic progression that matches the energy of your music perfectly!"""
    
    print("📝 Simulated AI Response:")
    print(f"{ai_response}\n")
    
    # Step 1: Extract ACTION proposals
    print("Step 1: Extracting ACTION proposals...")
    cleaned_response, action_proposals = extract_action_proposals(ai_response)
    
    print(f"✅ Extracted {len(action_proposals)} ACTION proposals")
    print(f"Cleaned response length: {len(cleaned_response)} chars")
    
    # Step 2: Show what user would see
    print(f"\nStep 2: User confirmation prompt:")
    if action_proposals:
        print("**I want to make these lighting changes:**")
        for action in action_proposals:
            if action.get('can_execute', False):
                print(f"• {action.get('description', action.get('command', 'Unknown action'))}")
        print("\nDo you want me to execute these changes? Please reply 'yes' to confirm or 'no' to cancel.")
    
    # Step 3: Simulate user confirmation and execute
    print(f"\nStep 3: Simulating user confirmation ('yes')...")
    results = []
    any_success = False
    
    for action in action_proposals:
        if action.get('can_execute', False):
            try:
                success, message = execute_confirmed_action(action['id'], action_proposals)
                results.append(f"✓ {message}" if success else f"✗ {message}")
                if success:
                    any_success = True
                print(f"🎭 ACTION EXECUTED: {action['command']} -> {'SUCCESS' if success else 'FAILED'}: {message}")
            except Exception as e:
                results.append(f"✗ Error: {str(e)}")
                print(f"❌ Error executing action {action['id']}: {str(e)}")
    
    print(f"\n🏁 Integration test completed!")
    print(f"Results: {len([r for r in results if r.startswith('✓')])} successes, {len([r for r in results if r.startswith('✗')])} failures")
    
    if any_success:
        print("✅ At least one action executed successfully - integration is working!")
    else:
        print("❌ No actions executed successfully - integration needs investigation")

def test_common_mistral_patterns():
    """Test patterns commonly generated by Mistral AI."""
    print("\n🤖 Testing common Mistral AI patterns...")
    print("=" * 60)
    
    test_song = setup_test_environment()
    
    # These are realistic ACTION commands that Mistral might generate
    mistral_patterns = [
        # Basic commands
        "Add white flash preset at 67.3s using both parcans",
        "Add red and blue pulse effect during the drop using all RGB fixtures",
        
        # Complex timing
        "Add fast white strobe for 8 beats during the breakdown using Head EL-150",
        "Add warm orange glow from 90s to 120s using left side lights",
        
        # Multiple fixture types
        "Add rainbow chase effect during the chorus using all fixtures",
        "Add green flash on beat hits during the verse using both protons",
        
        # Duration-based
        "Add slow blue fade for 16 beats at the bridge using moving heads",
        
        # Removal commands
        "Remove all lighting cues between 45s and 60s",
    ]
    
    print("Testing Mistral-style ACTION commands:")
    
    for i, command in enumerate(mistral_patterns, 1):
        print(f"\n📝 Pattern {i}: {command}")
        print("-" * 40)
        
        # Simulate the full flow
        fake_response = f"I'll create that effect for you.\n\nACTION: {command}\n\nThis will look great!"
        
        try:
            cleaned_response, action_proposals = extract_action_proposals(fake_response)
            
            if action_proposals:
                proposal = action_proposals[0]
                print(f"✅ Extracted: {proposal.get('command')}")
                print(f"   Can execute: {proposal.get('can_execute')}")
                print(f"   Description: {proposal.get('description')}")
                
                if proposal.get('can_execute'):
                    success, message = execute_confirmed_action(proposal['id'], action_proposals)
                    print(f"🎯 Execution: {'✅ SUCCESS' if success else '❌ FAILED'}")
                    print(f"   Result: {message}")
                else:
                    print(f"❌ Cannot execute: {proposal.get('error', 'Unknown error')}")
            else:
                print("❌ No ACTION proposals extracted")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Mistral ACTION Integration Test Suite")
    print("=" * 80)
    
    try:
        test_action_extraction()
        test_cue_interpreter_integration() 
        test_full_integration_flow()
        test_common_mistral_patterns()
        
        print("\n" + "=" * 80)
        print("🎉 Test suite completed!")
        print("If you see any failures above, those indicate areas where")
        print("Mistral ACTION commands might not be working as expected.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
