"""Natural language cue interpreter for AI Light Show system."""

import re
from typing import Dict, List, Optional, Tuple
from ..models.song_metadata import SongMetadata
from ..services.cue_service import CueManager

class CueInterpreter:
    """Interprets natural language commands and converts them to cue operations."""
    
    def __init__(self, cue_manager: CueManager):
        self.cue_manager = cue_manager
        
    def parse_time_reference(self, text: str, song: SongMetadata) -> Optional[float]:
        """Parse time references like 'at the drop', 'during chorus', '2:30'."""
        
        # Direct time references (MM:SS or seconds)
        time_patterns = [
            r'(?:at\s+)?(\d+):(\d+)',  # MM:SS format
            r'(?:at\s+)?(\d+(?:\.\d+)?)\s*(?:s|sec|second)',  # Direct seconds
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if ':' in match.group(0):
                    minutes, seconds = map(float, match.groups())
                    return minutes * 60 + seconds
                else:
                    return float(match.group(1))
        
        # Musical section references
        section_patterns = [
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?drop', 'drop'),
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?chorus', 'chorus'),
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?verse', 'verse'),
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?bridge', 'bridge'),
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?intro', 'intro'),
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?outro', 'outro'),
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?breakdown', 'breakdown'),
            (r'(?:at\s+the\s+|during\s+the\s+|in\s+the\s+)?build', 'build'),
            (r'(?:during\s+the\s+)?(?:syncopated\s+)?energy\s+boost', 'energy_boost'),
            (r'(?:during\s+the\s+)?(?:toms?\s+and\s+)?hihats?\s+pattern', 'drums_pattern'),
            (r'(?:during\s+the\s+)?(?:exit\s+)?bridge\s+and\s+outro', 'bridge'),
            (r'(?:on\s+)?beat\s+hits?', 'beat_hits'),
            (r'for\s+(\d+)\s+beats?', 'beat_duration'),
            (r'every\s+(\d+)\s+beats?', 'beat_interval'),
        ]
        
        for pattern, section_type in section_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Handle beat-based timing references
                if section_type == 'beat_hits':
                    # For beat hits, find the next appropriate beat location
                    if hasattr(song, 'beats') and song.beats:
                        # Use first beat as starting point
                        return song.beats[0].get('time', 0.0) if isinstance(song.beats[0], dict) else song.beats[0]
                    return 0.0  # Default to start
                elif section_type == 'beat_duration':
                    # For "X beats" duration, use current playback time or verse start
                    from ..models.app_state import app_state
                    if app_state.playback.playback_time > 0:
                        return app_state.playback.playback_time
                    # Default to verse timing if available
                    time = self._find_section_time('verse', song)
                    return time if time is not None else 10.0
                elif section_type == 'beat_interval':
                    # For "every X beats", use verse or current timing
                    from ..models.app_state import app_state
                    if app_state.playback.playback_time > 0:
                        return app_state.playback.playback_time
                    time = self._find_section_time('verse', song)
                    return time if time is not None else 10.0
                
                # Find matching section or key moment
                time = self._find_section_time(section_type, song)
                if time is not None:
                    return time
                # If section not found, use smart defaults based on section type
                if section_type == 'drop':
                    # For electronic music, drop is often around 30% into the song
                    if hasattr(song, 'duration') and song.duration:
                        return song.duration * 0.3
                    return 30.0  # Default fallback
                elif section_type == 'bridge':
                    # Bridge is typically in the middle-to-later part
                    if hasattr(song, 'duration') and song.duration:
                        return song.duration * 0.6
                    return 60.0
                elif section_type == 'chorus':
                    # First chorus often early in song
                    if hasattr(song, 'duration') and song.duration:
                        return song.duration * 0.2
                    return 20.0
                elif section_type == 'energy_boost':
                    # Energy boost often in middle section
                    if hasattr(song, 'duration') and song.duration:
                        return song.duration * 0.4
                    return 40.0
                elif section_type == 'drums_pattern':
                    # Drum patterns often in latter half
                    if hasattr(song, 'duration') and song.duration:
                        return song.duration * 0.5
                    return 50.0
        
        return None
    
    def _find_section_time(self, section_type: str, song: SongMetadata) -> Optional[float]:
        """Find the start time of a musical section."""
        
        # Check arrangement sections first
        if hasattr(song, 'arrangement') and song.arrangement:
            for section in song.arrangement:
                section_name = getattr(section, 'name', '').lower()
                if section_type in section_name:
                    return getattr(section, 'start', None)
        
        # Check key moments
        if hasattr(song, 'key_moments') and song.key_moments:
            for moment in song.key_moments:
                if isinstance(moment, dict):
                    name = moment.get('name', '').lower()
                    description = moment.get('description', '').lower()
                    if section_type in name or section_type in description:
                        return moment.get('time')
        
        return None
    
    def parse_fixture_reference(self, text: str, available_fixtures: List[Dict]) -> List[str]:
        """Parse fixture references like 'all lights', 'moving heads', 'parcan left'."""
        
        fixture_ids = []
        
        # All fixtures
        if re.search(r'\b(?:all|every)\s+(?:lights?|fixtures?|parcans?)\b', text, re.IGNORECASE):
            return [f['id'] for f in available_fixtures]
        
        # By type
        type_patterns = [
            (r'\bmoving\s+heads?\b', 'moving_head'),
            (r'\bparcans?\b', 'rgb'),
            (r'\brgb\s+lights?\b', 'rgb'),
            (r'\bspots?\b', 'moving_head'),
        ]
        
        for pattern, fixture_type in type_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                fixture_ids.extend([
                    f['id'] for f in available_fixtures 
                    if f.get('type') == fixture_type
                ])
        
        # Special handling for "parcans" mentioned in logs
        if re.search(r'\bparcans?\b', text, re.IGNORECASE):
            # Add any fixture with "parcan" in the name or ID
            fixture_ids.extend([
                f['id'] for f in available_fixtures 
                if 'parcan' in f.get('id', '').lower() or 'parcan' in f.get('name', '').lower()
            ])
        
        # Directional references
        if re.search(r'\bright[-\s]?side\b', text, re.IGNORECASE):
            fixture_ids.extend([
                f['id'] for f in available_fixtures 
                if any(side in f.get('id', '').lower() for side in ['_r', '_pr', 'right'])
            ])
        
        if re.search(r'\bleft[-\s]?side\b', text, re.IGNORECASE):
            fixture_ids.extend([
                f['id'] for f in available_fixtures 
                if any(side in f.get('id', '').lower() for side in ['_l', '_pl', 'left'])
            ])
        
        if re.search(r'\bleft\s+and\s+right\b', text, re.IGNORECASE) or re.search(r'\bmirrored\s+left\s+and\s+right\b', text, re.IGNORECASE):
            fixture_ids.extend([
                f['id'] for f in available_fixtures 
                if any(side in f.get('id', '').lower() for side in ['_l', '_pl', 'left', '_r', '_pr', 'right'])
            ])
        
        # By specific name/id
        for fixture in available_fixtures:
            fixture_name = fixture.get('name', '').lower()
            fixture_id = fixture.get('id', '').lower()
            
            # Check if fixture name or id appears in text
            if (fixture_name and fixture_name in text.lower()) or \
               (fixture_id and fixture_id in text.lower()):
                fixture_ids.append(fixture['id'])
        
        return list(set(fixture_ids))  # Remove duplicates
    
    def parse_effect_parameters(self, text: str) -> Dict:
        """Parse effect parameters like 'bright red', 'slow fade', 'intense strobe'."""
        
        params = {}
        
        # Colors
        color_patterns = [
            (r'\b(?:bright\s+|deep\s+|light\s+)?red\b', {'red': 255, 'green': 0, 'blue': 0}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?blue\b', {'red': 0, 'green': 0, 'blue': 255}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?green\b', {'red': 0, 'green': 255, 'blue': 0}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?white\b', {'red': 255, 'green': 255, 'blue': 255}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?yellow\b', {'red': 255, 'green': 255, 'blue': 0}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?purple\b', {'red': 255, 'green': 0, 'blue': 255}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?cyan\b', {'red': 0, 'green': 255, 'blue': 255}),
        ]
        
        for pattern, color_values in color_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                params.update(color_values)
                break
        
        # Intensity modifiers
        if re.search(r'\b(?:bright|intense|full|maximum)\b', text, re.IGNORECASE):
            params['intensity'] = 1.0
        elif re.search(r'\b(?:dim|low|soft|gentle)\b', text, re.IGNORECASE):
            params['intensity'] = 0.3
        elif re.search(r'\b(?:medium|normal)\b', text, re.IGNORECASE):
            params['intensity'] = 0.6
        
        # Speed modifiers
        if re.search(r'\b(?:fast|quick|rapid)\b', text, re.IGNORECASE):
            params['speed'] = 'fast'
        elif re.search(r'\b(?:slow|gentle|gradual)\b', text, re.IGNORECASE):
            params['speed'] = 'slow'
        
        # Effect types
        if re.search(r'\b(?:flash|strobe|blink)\b', text, re.IGNORECASE):
            params['effect_type'] = 'flash'
        elif re.search(r'\b(?:fade|transition)\b', text, re.IGNORECASE):
            params['effect_type'] = 'fade'
        elif re.search(r'\b(?:chase|sequence|chasers?)\b', text, re.IGNORECASE):
            params['effect_type'] = 'chase'
        elif re.search(r'\bpulse\b', text, re.IGNORECASE):
            params['effect_type'] = 'flash'  # Pulse can use flash preset
        elif re.search(r'\bmulti[-\s]?colored?\b', text, re.IGNORECASE):
            params['effect_type'] = 'chase'  # Multi-colored often implies sequence
        
        # Handle specific effect combinations
        if re.search(r'\bmulti[-\s]?colored?\s+strobes?\b', text, re.IGNORECASE):
            params['effect_type'] = 'flash'
            params['multi_color'] = True
        
        if re.search(r'\bfast\s+chasers?\b', text, re.IGNORECASE):
            params['effect_type'] = 'chase'
            params['speed'] = 'fast'
        
        return params
    
    def interpret_command(self, command: str, song: SongMetadata, available_fixtures: List[Dict], available_presets: List[Dict]) -> Dict:
        """Interpret a natural language command and return cue operation."""
        
        command = command.strip().lower()
        print(f"🔍 Interpreting command: '{command}'")
        
        if not command:
            raise ValueError("Empty command provided")
        
        if not song:
            raise ValueError("No song metadata available")
        
        if not available_fixtures:
            raise ValueError("No fixtures available")
        
        if not available_presets:
            raise ValueError("No presets available")
        
        # Determine operation type
        if any(word in command for word in ['add', 'create', 'set', 'turn on', 'activate']):
            operation = 'add'
        elif any(word in command for word in ['remove', 'delete', 'turn off', 'stop']):
            operation = 'remove'
        elif any(word in command for word in ['change', 'modify', 'update', 'adjust']):
            operation = 'modify'
        else:
            operation = 'add'  # Default to add
        
        # Parse components
        time_ref = self.parse_time_reference(command, song)
        fixture_ids = self.parse_fixture_reference(command, available_fixtures)
        effect_params = self.parse_effect_parameters(command)
        
        print(f"🔍 Parsed components:")
        print(f"   Operation: {operation}")
        print(f"   Time reference: {time_ref}")
        print(f"   Fixture IDs: {fixture_ids}")
        print(f"   Effect params: {effect_params}")
        
        # Find best matching preset
        preset_name = self._find_best_preset(effect_params, available_presets)
        print(f"   Selected preset: {preset_name}")
        
        # Validation
        if operation == 'add' and time_ref is None:
            # Try to use current playback time or default to start
            from ..models.app_state import app_state
            time_ref = app_state.playback.playback_time if app_state.playback.playback_time > 0 else 0.0
            print(f"   Using fallback time: {time_ref}")
        
        # If no fixtures identified but command mentions lights/fixtures, use all
        if not fixture_ids and re.search(r'\b(?:lights?|fixtures?|parcans?|all)\b', command, re.IGNORECASE):
            # Use RGB fixtures as default for color commands
            if any(color in command for color in ['red', 'blue', 'green', 'white', 'yellow', 'purple', 'cyan']):
                fixture_ids = [f['id'] for f in available_fixtures if f.get('type') == 'rgb']
                print(f"   Using RGB fixtures for color command: {fixture_ids}")
            else:
                # Use all fixtures as fallback
                fixture_ids = [f['id'] for f in available_fixtures]
                print(f"   Using all fixtures as fallback: {fixture_ids}")
        
        # If still no fixtures but we have effect commands (strobe, chase, fade), use all RGB fixtures
        if not fixture_ids and any(effect in command for effect in ['strobe', 'chase', 'fade', 'flash', 'pulse']):
            fixture_ids = [f['id'] for f in available_fixtures if f.get('type') == 'rgb']
            print(f"   Using RGB fixtures for effect command: {fixture_ids}")
        
        return {
            'operation': operation,
            'time': time_ref,
            'fixtures': fixture_ids,
            'preset': preset_name,
            'parameters': effect_params,
            'raw_command': command,
            'confidence': self._calculate_confidence(command, time_ref, fixture_ids, preset_name)
        }
    
    def _find_best_preset(self, effect_params: Dict, available_presets: List[Dict]) -> Optional[str]:
        """Find the best matching preset based on effect parameters."""
        
        effect_type = effect_params.get('effect_type')
        
        # Simple preset matching logic
        preset_mapping = {
            'flash': ['flash', 'strobe', 'blink'],
            'fade': ['fade', 'transition', 'smooth'],
            'chase': ['chase', 'sequence', 'runner']
        }
        
        if effect_type and effect_type in preset_mapping:
            keywords = preset_mapping[effect_type]
            for preset in available_presets:
                preset_name = preset.get('name', '').lower()
                if any(keyword in preset_name for keyword in keywords):
                    return preset['name']
        
        # Look for specific preset names (case-insensitive)
        for preset in available_presets:
            preset_name = preset.get('name', '').lower()
            if effect_type and effect_type in preset_name:
                return preset['name']
        
        # Default presets based on parameters
        if 'red' in effect_params or 'green' in effect_params or 'blue' in effect_params:
            # Look for color-based presets first
            for preset in available_presets:
                preset_name = preset.get('name', '').lower()
                if any(word in preset_name for word in ['color', 'rgb', 'flash']):
                    return preset['name']
        
        # Look for flash preset specifically
        for preset in available_presets:
            if 'flash' in preset.get('name', '').lower():
                return preset['name']
        
        # Fallback to first available preset
        return available_presets[0]['name'] if available_presets else None

    def execute_command(self, command: str, song: SongMetadata, available_fixtures: List[Dict], available_presets: List[Dict]) -> Tuple[bool, str]:
        """Execute a natural language command and return success status and message."""
        
        try:
            interpretation = self.interpret_command(command, song, available_fixtures, available_presets)
            
            if interpretation['operation'] == 'add':
                return self._execute_add_command(interpretation)
            elif interpretation['operation'] == 'remove':
                return self._execute_remove_command(interpretation)
            elif interpretation['operation'] == 'modify':
                return self._execute_modify_command(interpretation)
            else:
                return False, f"Unknown operation: {interpretation['operation']}"
                
        except Exception as e:
            return False, f"Error executing command: {str(e)}"
    
    def _execute_add_command(self, interpretation: Dict) -> Tuple[bool, str]:
        """Execute an add cue command."""
        
        print(f"🔍 Executing add command:")
        print(f"   Time: {interpretation['time']}")
        print(f"   Fixtures: {interpretation['fixtures']}")
        print(f"   Preset: {interpretation['preset']}")
        print(f"   Parameters: {interpretation['parameters']}")
        
        if not interpretation['time']:
            return False, "Could not determine timing for the cue"
        
        if not interpretation['fixtures']:
            return False, "Could not identify which fixtures to control"
        
        if not interpretation['preset']:
            return False, "Could not find a suitable preset"
        
        cues_added = 0
        for fixture_id in interpretation['fixtures']:
            cue = {
                'time': interpretation['time'],
                'fixture': fixture_id,
                'preset': interpretation['preset'],
                'parameters': interpretation['parameters']
            }
            self.cue_manager.add_cue(cue)
            cues_added += 1
        
        return True, f"Added {cues_added} cue(s) at {interpretation['time']:.1f}s using preset '{interpretation['preset']}'"
    
    def _execute_remove_command(self, interpretation: Dict) -> Tuple[bool, str]:
        """Execute a remove cue command."""
        
        # Implementation depends on CueManager's remove capabilities
        # This is a simplified version
        removed_count = 0
        
        if interpretation['time'] and interpretation['fixtures']:
            for fixture_id in interpretation['fixtures']:
                self.cue_manager.delete_cue(fixture_id, interpretation['time'])
                removed_count += 1
        
        return True, f"Removed {removed_count} cue(s)"
    
    def _execute_modify_command(self, interpretation: Dict) -> Tuple[bool, str]:
        """Execute a modify cue command."""
        
        # This would require more sophisticated cue modification logic
        return False, "Cue modification not yet implemented"
    
    def _calculate_confidence(self, command: str, time_ref: Optional[float], fixture_ids: List[str], preset_name: Optional[str]) -> float:
        """Calculate confidence score for command interpretation (0.0 to 1.0)."""
        
        confidence = 0.0
        
        # Time reference confidence
        if time_ref is not None:
            confidence += 0.3
        
        # Fixture identification confidence
        if fixture_ids:
            confidence += 0.3
        
        # Preset matching confidence
        if preset_name:
            confidence += 0.2
        
        # Command clarity confidence (basic keyword matching)
        clear_keywords = ['add', 'remove', 'flash', 'fade', 'red', 'blue', 'green', 'white', 'drop', 'chorus', 'verse']
        found_keywords = sum(1 for keyword in clear_keywords if keyword in command.lower())
        confidence += min(0.2, found_keywords * 0.05)
        
        return min(1.0, confidence)
