"""Action proposal extraction and execution for Ollama AI responses."""

import re
from typing import Dict, List, Tuple
from ...models.app_state import app_state
from .ollama_instructions import load_fixture_config


def extract_action_proposals(ai_response: str, session_id: str = "default"):
    """Extract ACTION commands from AI response and prepare them for user confirmation."""
    
    # Extract ACTION commands from response and remove them from display
    action_pattern = r'ACTION:\s*(.+?)(?:\n|$)'
    actions = re.findall(action_pattern, ai_response, re.IGNORECASE | re.MULTILINE)
    
    # Remove ACTION lines from the response that will be shown to user
    cleaned_response = re.sub(action_pattern, '', ai_response, flags=re.IGNORECASE | re.MULTILINE).strip()
    
    if not actions:
        return cleaned_response, []
    
    # Get current context
    current_song = app_state.current_song
    if not current_song:
        return cleaned_response, [{"error": "No song loaded - cannot create lighting actions"}]

    fixtures, presets = load_fixture_config()

    proposals = []
    for action_text in actions:
        try:
            # Create a more detailed proposal with better description
            proposal = {
                "id": f"action_{len(proposals)}",
                "command": action_text.strip(),
                "description": _generate_friendly_description(action_text.strip(), fixtures, presets),
                "confidence": 0.8,
                "can_execute": True,
                "raw_command": action_text.strip()
            }
            proposals.append(proposal)
            
        except Exception as e:
            proposals.append({
                "id": f"action_{len(proposals)}",
                "command": action_text.strip(),
                "error": str(e),
                "description": f"Could not interpret command: {action_text}",
                "confidence": 0.0,
                "can_execute": False
            })
    
    return cleaned_response, proposals


def execute_confirmed_action(action_id: str, proposals: List[Dict]) -> Tuple[bool, str]:
    """
    Execute a confirmed action from the proposals list using the Actions system.
    
    Follows the Actions-Based Flow: AI → Actions Sheet → Actions Service → DMX Canvas
    Uses cached services from app_state to avoid re-initialization (performance optimization).
    
    Args:
        action_id: ID of the action to execute from proposals
        proposals: List of action proposals from AI response
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    
    # Find the action by ID
    action = next((p for p in proposals if p.get('id') == action_id), None)
    if not action:
        return False, f"Action {action_id} not found"
    
    if not action.get('can_execute', False):
        return False, f"Action cannot be executed: {action.get('error', 'Unknown error')}"
    
    # Get current context from global app_state
    current_song = app_state.current_song
    if not current_song:
        return False, "No song loaded - Actions system requires an active song"
    
    # Import required modules
    from ...models.actions_sheet import ActionsSheet
    from pathlib import Path
    from ...services.websocket_service import broadcast_to_all
    import asyncio
    
    try:
        # Get the action command from the proposal
        action_command = action.get('command', '').strip()
        if not action_command:
            return False, "Empty action command"
        
        # Get song name from the current song file
        song_name = Path(current_song.file_name).stem
        
        # Get fixtures from app state
        fixtures = app_state.fixtures
        if not fixtures:
            return False, "No fixtures configured"
        
        # Use cached parser service from app_state to avoid re-initialization
        parser = app_state.get_actions_parser_service()
        if not parser:
            return False, "Failed to initialize actions parser service"
        
        # Parse the action command
        parsed_actions = parser.parse_command(action_command)
        if not parsed_actions:
            return False, f"Failed to parse action command: {action_command}"
        
        # Initialize the actions sheet for current song (Actions system)
        actions_sheet = ActionsSheet(song_name)
        actions_sheet.load_actions()
        
        # Add all parsed actions to the actions sheet (replaces old cue system)
        for parsed_action in parsed_actions:
            actions_sheet.add_action(parsed_action)
        
        # Save the updated actions sheet
        if actions_sheet.save_actions():
            # Convert actions to dicts for JSON serialization
            actions_json = [action.to_dict() for action in actions_sheet.actions]
            
            # Broadcast the update asynchronously
            asyncio.create_task(broadcast_to_all({
                "type": "actionsUpdate",
                "actions": actions_json
            }))
            
            # Render the actions to the DMX canvas using cached service
            if app_state.dmx_canvas:
                actions_service = app_state.get_actions_service()
                if actions_service:
                    actions_service.render_actions_to_canvas(actions_sheet, clear_first=False)
                else:
                    print("⚠️  Warning: Could not get actions service for DMX rendering")
            
            return True, f"Added {len(parsed_actions)} action(s) to the light show"
        else:
            return False, "Failed to save actions"
        
    except Exception as e:
        import traceback
        print(f"❌ Error executing action: {e}")
        print(traceback.format_exc())
        return False, f"Error executing action: {str(e)}"


def _generate_friendly_description(command: str, fixtures: List[Dict], presets: List[Dict]) -> str:
    """Generate a user-friendly description of what the command will do."""
    
    command_lower = command.lower()
    
    # Extract common patterns from the command
    description_parts = []
    
    # Look for operation type
    if any(word in command_lower for word in ['add', 'create', 'make']):
        description_parts.append("Add")
    elif any(word in command_lower for word in ['remove', 'delete', 'clear']):
        description_parts.append("Remove")
    elif any(word in command_lower for word in ['change', 'update', 'modify']):
        description_parts.append("Change")
    else:
        description_parts.append("Create")
    
    # Look for colors
    colors_found = []
    color_map = {
        'red': 'red', 'blue': 'blue', 'green': 'green', 'white': 'white', 
        'yellow': 'yellow', 'purple': 'purple', 'orange': 'orange', 
        'cyan': 'cyan', 'magenta': 'magenta', 'pink': 'pink'
    }
    
    for color_word, color_name in color_map.items():
        if color_word in command_lower:
            colors_found.append(color_name)
    
    # Look for effects
    effects_found = []
    effect_keywords = {
        'flash': 'flash effect', 'strobe': 'strobe effect', 'pulse': 'pulse effect',
        'fade': 'fade effect', 'chase': 'chase sequence', 'sweep': 'sweep effect',
        'dim': 'dimming', 'bright': 'bright lights', 'slow': 'slow effect',
        'fast': 'fast effect', 'smooth': 'smooth transition'
    }
    
    for keyword, effect_name in effect_keywords.items():
        if keyword in command_lower:
            effects_found.append(effect_name)
    
    # Look for timing references
    timing_found = []
    if any(word in command_lower for word in ['drop', 'bass drop']):
        timing_found.append("at the drop")
    elif any(word in command_lower for word in ['chorus']):
        timing_found.append("during the chorus")
    elif any(word in command_lower for word in ['verse']):
        timing_found.append("during the verse")
    elif any(word in command_lower for word in ['bridge']):
        timing_found.append("during the bridge")
    elif any(word in command_lower for word in ['intro']):
        timing_found.append("during the intro")
    elif any(word in command_lower for word in ['outro', 'ending']):
        timing_found.append("at the ending")
    
    # Look for fixture types
    fixtures_found = []
    fixture_keywords = {
        'parcan': 'parcan lights', 'moving': 'moving head lights', 'head': 'moving head lights',
        'spot': 'spotlight', 'wash': 'wash lights', 'strobe': 'strobe lights',
        'led': 'LED lights', 'laser': 'laser lights'
    }
    
    for keyword, fixture_name in fixture_keywords.items():
        if keyword in command_lower:
            fixtures_found.append(fixture_name)
    
    # Look for preset names
    preset_names = []
    for preset in presets[:10]:  # Check first 10 presets
        preset_name = preset.get('name', '').lower()
        if preset_name and preset_name in command_lower:
            preset_names.append(f"'{preset['name']}' preset")
    
    # Build the description
    description = description_parts[0]
    
    if colors_found:
        description += f" {' and '.join(colors_found)}"
    
    if effects_found:
        description += f" {' and '.join(effects_found)}"
    elif preset_names:
        description += f" {' and '.join(preset_names)}"
    
    if fixtures_found:
        description += f" using {' and '.join(fixtures_found)}"
    
    if timing_found:
        description += f" {' and '.join(timing_found)}"
    
    # Fallback to command text if description is too minimal
    if len(description.split()) < 3:
        description = f"Execute lighting command: {command}"
    
    return description.strip()


def _format_action_description(interpretation: Dict) -> str:
    """Format an action interpretation into a user-friendly description."""
    
    operation = interpretation.get('operation', 'unknown')
    time_ref = interpretation.get('time')
    fixtures = interpretation.get('fixtures', [])
    preset = interpretation.get('preset')
    params = interpretation.get('parameters', {})
    
    description = f"{operation.title()} "
    
    # Add effect description
    if preset:
        description += f"'{preset}' effect "
    
    # Add color info if available
    colors = []
    if params.get('red') == 255 and params.get('green') == 0 and params.get('blue') == 0:
        colors.append("red")
    elif params.get('red') == 0 and params.get('green') == 0 and params.get('blue') == 255:
        colors.append("blue")
    elif params.get('red') == 0 and params.get('green') == 255 and params.get('blue') == 0:
        colors.append("green")
    elif params.get('red') == 255 and params.get('green') == 255 and params.get('blue') == 255:
        colors.append("white")
    
    if colors:
        description += f"in {', '.join(colors)} "
    
    # Add fixture info
    if len(fixtures) == 1:
        description += f"on {fixtures[0]} "
    elif len(fixtures) > 1:
        description += f"on {len(fixtures)} fixtures "
    
    # Add timing info
    if time_ref is not None:
        description += f"at {time_ref:.1f}s"
    
    return description.strip()
