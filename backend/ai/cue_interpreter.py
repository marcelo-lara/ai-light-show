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
        
        # Direct channel value specifications
        channel_patterns = [
            (r'\bred\s+(?:to\s+|at\s+)?(\d+)', 'red'),
            (r'\bgreen\s+(?:to\s+|at\s+)?(\d+)', 'green'),
            (r'\bblue\s+(?:to\s+|at\s+)?(\d+)', 'blue'),
            (r'\bdim(?:mer)?\s+(?:to\s+|at\s+)?(\d+)', 'dim'),
            (r'\bstrobe\s+(?:to\s+|at\s+)?(\d+)', 'strobe'),
            (r'\bpan\s+(?:to\s+|at\s+)?(\d+)', 'pan'),
            (r'\btilt\s+(?:to\s+|at\s+)?(\d+)', 'tilt'),
        ]
        
        for pattern, channel in channel_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                params[f'channel_{channel}'] = int(match.group(1))
        
        # Percentage-based channel values
        percentage_patterns = [
            (r'\bred\s+(?:to\s+|at\s+)?(\d+)%', 'red'),
            (r'\bgreen\s+(?:to\s+|at\s+)?(\d+)%', 'green'),
            (r'\bblue\s+(?:to\s+|at\s+)?(\d+)%', 'blue'),
            (r'\bdim(?:mer)?\s+(?:to\s+|at\s+)?(\d+)%', 'dim'),
            (r'\bbrightness\s+(?:to\s+|at\s+)?(\d+)%', 'dim'),
            (r'\bintensity\s+(?:to\s+|at\s+)?(\d+)%', 'dim'),
        ]
        
        for pattern, channel in percentage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                percentage = int(match.group(1))
                params[f'channel_{channel}'] = int(255 * percentage / 100)
        
        # Color names with automatic RGB channel mapping
        # Only apply these if there's an explicit "set" command or direct channel specification
        explicit_channel_commands = [
            r'\bset\s+.*(?:red|green|blue|white|yellow|purple|cyan|orange|pink)\b',
            r'\b(?:red|green|blue|white|yellow|purple|cyan|orange|pink)\s+(?:to\s+|at\s+)?\d+',
            r'\b(?:red|green|blue|white|yellow|purple|cyan|orange|pink)\s+(?:to\s+|at\s+)?\d+%',
        ]
        
        has_explicit_channel_command = any(re.search(pattern, text, re.IGNORECASE) for pattern in explicit_channel_commands)
        
        color_patterns = [
            (r'\b(?:bright\s+|deep\s+|light\s+)?red\b', {'channel_red': 255, 'channel_green': 0, 'channel_blue': 0}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?blue\b', {'channel_red': 0, 'channel_green': 0, 'channel_blue': 255}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?green\b', {'channel_red': 0, 'channel_green': 255, 'channel_blue': 0}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?white\b', {'channel_red': 255, 'channel_green': 255, 'channel_blue': 255}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?yellow\b', {'channel_red': 255, 'channel_green': 255, 'channel_blue': 0}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?purple\b', {'channel_red': 255, 'channel_green': 0, 'channel_blue': 255}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?cyan\b', {'channel_red': 0, 'channel_green': 255, 'channel_blue': 255}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?orange\b', {'channel_red': 255, 'channel_green': 165, 'channel_blue': 0}),
            (r'\b(?:bright\s+|deep\s+|light\s+)?pink\b', {'channel_red': 255, 'channel_green': 192, 'channel_blue': 203}),
        ]
        
        # Only apply channel-based color mapping if there's an explicit channel command
        should_apply_channel_colors = (
            not any(key.startswith('channel_') for key in params.keys()) and
            has_explicit_channel_command
        )
        
        if should_apply_channel_colors:
            for pattern, color_values in color_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    params.update(color_values)
                    # Auto-set dimmer for colored lights
                    if 'channel_dim' not in params:
                        params['channel_dim'] = 255
                    break
        
        # Add strobe channel for explicit strobe commands
        if re.search(r'\bstrobe\b', text, re.IGNORECASE) and 'channel_strobe' not in params:
            # Only add automatic strobe channel if we're in channel mode
            if any(key.startswith('channel_') for key in params.keys()):
                params['channel_strobe'] = 150  # Default strobe value
        
        # Position specifications for moving heads
        position_patterns = [
            (r'\bpan\s+(?:to\s+)?(\d+)\s*(?:degrees?|deg|°)', 'pan'),
            (r'\btilt\s+(?:to\s+)?(\d+)\s*(?:degrees?|deg|°)', 'tilt'),
            (r'\bposition\s+(\d+),\s*(\d+)', 'pan_tilt'),  # pan,tilt format
        ]
        
        for pattern, pos_type in position_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if pos_type == 'pan_tilt':
                    params['channel_pan'] = int(255 * int(match.group(1)) / 360)  # Convert degrees to 0-255
                    params['channel_tilt'] = int(255 * int(match.group(2)) / 360)
                elif pos_type == 'pan':
                    params['channel_pan'] = int(255 * int(match.group(1)) / 360)
                elif pos_type == 'tilt':
                    params['channel_tilt'] = int(255 * int(match.group(1)) / 360)
        
        # Duration and repeat patterns
        duration_patterns = [
            (r'(?:for|lasting)\s+(\d+)\s+beats?', 'beat_duration'),
            (r'(?:for|lasting)\s+(\d+)\s+(?:seconds?|s)', 'time_duration'),
            (r'every\s+(\d+)\s+beats?', 'beat_interval'),
            (r'every\s+beat', 'beat_interval_1'),
            (r'(?:during|throughout)\s+(?:the\s+)?(?:entire\s+)?(?:drop|chorus|verse|bridge|section)', 'section_duration'),
        ]
        
        for pattern, duration_type in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if duration_type == 'beat_duration':
                    params['duration_beats'] = int(match.group(1))
                    params['repeat_mode'] = 'duration'
                elif duration_type == 'time_duration':
                    params['duration_seconds'] = float(match.group(1))
                    params['repeat_mode'] = 'duration'
                elif duration_type == 'beat_interval':
                    params['beat_interval'] = int(match.group(1))
                    params['repeat_mode'] = 'interval'
                elif duration_type == 'beat_interval_1':
                    params['beat_interval'] = 1
                    params['repeat_mode'] = 'interval'
                elif duration_type == 'section_duration':
                    params['repeat_mode'] = 'section'
                break
        
        # Repeating effect indicators
        if re.search(r'\b(?:repeatedly|continuously|constantly|throughout)\b', text, re.IGNORECASE):
            params['repeat_mode'] = params.get('repeat_mode', 'continuous')
        
        # Intensity modifiers (apply to dimmer if no specific channel set)
        if 'channel_dim' not in params:
            if re.search(r'\b(?:bright|intense|full|maximum)\b', text, re.IGNORECASE):
                params['channel_dim'] = 255
            elif re.search(r'\b(?:dim|low|soft|gentle)\b', text, re.IGNORECASE):
                params['channel_dim'] = 77  # 30% of 255
            elif re.search(r'\b(?:medium|normal)\b', text, re.IGNORECASE):
                params['channel_dim'] = 153  # 60% of 255
        
        # Speed modifiers for strobe
        if re.search(r'\b(?:fast|quick|rapid)\s+strobe\b', text, re.IGNORECASE):
            params['channel_strobe'] = 200
            params['speed'] = 'fast'
        elif re.search(r'\b(?:slow|gentle|gradual)\s+strobe\b', text, re.IGNORECASE):
            params['channel_strobe'] = 100
            params['speed'] = 'slow'
        elif re.search(r'\bstrobe\b', text, re.IGNORECASE) and 'channel_strobe' not in params:
            params['channel_strobe'] = 150  # Medium strobe
        
        # Effect types for fallback to presets
        if re.search(r'\b(?:flash|strobe|blink)\b', text, re.IGNORECASE):
            params['effect_type'] = 'flash'
            # Flash effects often imply repetition if no specific mode set
            if 'repeat_mode' not in params:
                params['repeat_mode'] = 'beat_sync'
        elif re.search(r'\b(?:fade|transition)\b', text, re.IGNORECASE):
            params['effect_type'] = 'fade'
        elif re.search(r'\b(?:chase|sequence|chasers?)\b', text, re.IGNORECASE):
            params['effect_type'] = 'chase'
            # Chase effects are inherently repeating
            if 'repeat_mode' not in params:
                params['repeat_mode'] = 'continuous'
        elif re.search(r'\bpulse\b', text, re.IGNORECASE):
            params['effect_type'] = 'flash'  # Pulse can use flash preset
            if 'repeat_mode' not in params:
                params['repeat_mode'] = 'beat_sync'
        elif re.search(r'\bmulti[-\s]?colored?\b', text, re.IGNORECASE):
            params['effect_type'] = 'chase'  # Multi-colored often implies sequence
            if 'repeat_mode' not in params:
                params['repeat_mode'] = 'continuous'
        
        # Handle specific effect combinations
        if re.search(r'\bmulti[-\s]?colored?\s+strobes?\b', text, re.IGNORECASE):
            params['effect_type'] = 'flash'
            params['multi_color'] = True
            params['repeat_mode'] = 'beat_sync'
        
        if re.search(r'\bfast\s+chasers?\b', text, re.IGNORECASE):
            params['effect_type'] = 'chase'
            params['speed'] = 'fast'
            params['repeat_mode'] = 'continuous'
        
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
        elif any(word in command for word in ['remove', 'delete', 'turn off', 'stop', 'clear']):
            operation = 'remove'
        elif any(word in command for word in ['change', 'modify', 'update', 'adjust', 'replace', 'switch']):
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
        
        params = interpretation['parameters']
        repeat_mode = params.get('repeat_mode')
        
        # Check if we have direct channel commands
        has_channel_commands = any(key.startswith('channel_') for key in params.keys())
        
        if has_channel_commands:
            # Direct channel control - don't need a preset
            return self._create_channel_cues(interpretation)
        elif interpretation['preset']:
            # Preset-based control
            if repeat_mode and repeat_mode != 'single':
                return self._create_repeating_cues(interpretation)
            else:
                # Single cue execution
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
        else:
            return False, "Could not find a suitable preset or channel commands"
    
    def _create_channel_cues(self, interpretation: Dict) -> Tuple[bool, str]:
        """Create cues with direct channel control instead of presets."""
        
        params = interpretation['parameters']
        repeat_mode = params.get('repeat_mode')
        
        if repeat_mode and repeat_mode != 'single':
            return self._create_repeating_channel_cues(interpretation)
        else:
            # Single channel-based cue
            cues_added = 0
            channel_summary = []
            
            for fixture_id in interpretation['fixtures']:
                # Get fixture definition to map channel names to values
                fixtures, _, _ = self._get_fixture_config()
                fixture_def = next((f for f in fixtures if f['id'] == fixture_id), None)
                
                if not fixture_def:
                    continue
                
                # Build channel values for this fixture
                channel_values = {}
                for param_key, param_value in params.items():
                    if param_key.startswith('channel_'):
                        channel_name = param_key[8:]  # Remove 'channel_' prefix
                        if channel_name in fixture_def.get('channels', {}):
                            channel_values[channel_name] = param_value
                            if channel_name not in [item.split('=')[0] for item in channel_summary]:
                                channel_summary.append(f"{channel_name}={param_value}")
                
                if channel_values:
                    cue = {
                        'time': interpretation['time'],
                        'fixture': fixture_id,
                        'type': 'channel',  # Mark as direct channel control
                        'channels': channel_values,
                        'parameters': params
                    }
                    self.cue_manager.add_cue(cue)
                    cues_added += 1
            
            channel_desc = f" ({', '.join(channel_summary)})" if channel_summary else ""
            return True, f"Added {cues_added} channel cue(s) at {interpretation['time']:.1f}s{channel_desc}"
    
    def _create_repeating_channel_cues(self, interpretation: Dict) -> Tuple[bool, str]:
        """Create multiple channel-based cues for repeating effects."""
        
        params = interpretation['parameters']
        repeat_mode = params.get('repeat_mode')
        start_time = interpretation['time']
        
        # Get song info for beat calculations
        from ..models.app_state import app_state
        current_song = app_state.current_song
        bpm = getattr(current_song, 'bpm', 120) if current_song else 120
        beat_duration = 60.0 / bpm  # seconds per beat
        
        cue_times = []
        
        if repeat_mode == 'beat_sync':
            duration_beats = params.get('duration_beats', 8)
            for i in range(duration_beats):
                cue_times.append(start_time + (i * beat_duration))
        elif repeat_mode == 'interval':
            beat_interval = params.get('beat_interval', 1)
            duration_beats = params.get('duration_beats', 8)
            for i in range(0, duration_beats, beat_interval):
                cue_times.append(start_time + (i * beat_duration))
        elif repeat_mode == 'duration':
            if 'duration_beats' in params:
                total_duration = params['duration_beats'] * beat_duration
            elif 'duration_seconds' in params:
                total_duration = params['duration_seconds']
            else:
                total_duration = 8 * beat_duration
            
            beat_interval = params.get('beat_interval', 1)
            current_time = start_time
            while current_time < start_time + total_duration:
                cue_times.append(current_time)
                current_time += beat_interval * beat_duration
        else:
            cue_times = [start_time]
        
        # Create all the channel cues
        total_cues_added = 0
        channel_summary = []
        
        for fixture_id in interpretation['fixtures']:
            # Get fixture definition
            fixtures, _, _ = self._get_fixture_config()
            fixture_def = next((f for f in fixtures if f['id'] == fixture_id), None)
            
            if not fixture_def:
                continue
            
            # Build channel values
            channel_values = {}
            for param_key, param_value in params.items():
                if param_key.startswith('channel_'):
                    channel_name = param_key[8:]
                    if channel_name in fixture_def.get('channels', {}):
                        channel_values[channel_name] = param_value
                        if channel_name not in [item.split('=')[0] for item in channel_summary]:
                            channel_summary.append(f"{channel_name}={param_value}")
            
            for cue_time in cue_times:
                cue = {
                    'time': cue_time,
                    'fixture': fixture_id,
                    'type': 'channel',
                    'channels': channel_values.copy(),
                    'parameters': params.copy(),
                    'chaser': 'ai_repeating_channel',
                    'chaser_id': f"ai_ch_repeat_{fixture_id}_{start_time}"
                }
                self.cue_manager.add_cue(cue)
                total_cues_added += 1
        
        channel_desc = f" ({', '.join(channel_summary)})" if channel_summary else ""
        return True, f"Added {total_cues_added} repeating channel cues{channel_desc} starting at {start_time:.1f}s"
    
    def _get_fixture_config(self):
        """Helper to get fixture configuration - imports here to avoid circular deps."""
        try:
            from ..fixture_utils import load_fixtures_config
            return load_fixtures_config()
        except ImportError:
            # Fallback for testing
            return [], [], []
    
    def _create_repeating_cues(self, interpretation: Dict) -> Tuple[bool, str]:
        """Create multiple cues for repeating effects like strobes or beat-synced flashes."""
        
        params = interpretation['parameters']
        repeat_mode = params.get('repeat_mode')
        start_time = interpretation['time']
        
        # Get song info for beat calculations
        from ..models.app_state import app_state
        current_song = app_state.current_song
        bpm = getattr(current_song, 'bpm', 120) if current_song else 120
        beat_duration = 60.0 / bpm  # seconds per beat
        
        cue_times = []
        
        if repeat_mode == 'beat_sync':
            # Default beat-sync: flash every beat for 8 beats
            duration_beats = params.get('duration_beats', 8)
            for i in range(duration_beats):
                cue_times.append(start_time + (i * beat_duration))
                
        elif repeat_mode == 'interval':
            # Repeat at specified beat intervals
            beat_interval = params.get('beat_interval', 1)
            duration_beats = params.get('duration_beats', 8)  # Default duration
            
            for i in range(0, duration_beats, beat_interval):
                cue_times.append(start_time + (i * beat_duration))
                
        elif repeat_mode == 'duration':
            # Repeat for a specific duration
            if 'duration_beats' in params:
                total_duration = params['duration_beats'] * beat_duration
            elif 'duration_seconds' in params:
                total_duration = params['duration_seconds']
            else:
                total_duration = 8 * beat_duration  # Default 8 beats
            
            # Flash every beat within the duration
            beat_interval = params.get('beat_interval', 1)
            current_time = start_time
            while current_time < start_time + total_duration:
                cue_times.append(current_time)
                current_time += beat_interval * beat_duration
                
        elif repeat_mode == 'continuous':
            # Continuous effect (e.g., for chase sequences)
            # Create a longer-duration single cue with loop parameters
            duration_beats = params.get('duration_beats', 16)
            end_time = start_time + (duration_beats * beat_duration)
            cue_times = [start_time]
            
            # Add loop parameters to the preset
            params['loop_duration'] = duration_beats * beat_duration
            params['fade_beats'] = duration_beats
            
        elif repeat_mode == 'section':
            # Repeat throughout a musical section
            # This would need section timing analysis - for now, default to 16 beats
            duration_beats = 16
            for i in range(duration_beats):
                cue_times.append(start_time + (i * beat_duration))
        
        else:
            # Fallback: single cue
            cue_times = [start_time]
        
        # Create all the cues
        total_cues_added = 0
        for fixture_id in interpretation['fixtures']:
            for cue_time in cue_times:
                cue = {
                    'time': cue_time,
                    'fixture': fixture_id,
                    'preset': interpretation['preset'],
                    'parameters': params.copy(),  # Copy to avoid shared references
                    'chaser': 'ai_repeating',
                    'chaser_id': f"ai_repeat_{fixture_id}_{start_time}"
                }
                self.cue_manager.add_cue(cue)
                total_cues_added += 1
        
        # Generate descriptive message
        if repeat_mode == 'beat_sync':
            return True, f"Added {total_cues_added} beat-synced cues ({len(cue_times)} beats) starting at {start_time:.1f}s using '{interpretation['preset']}'"
        elif repeat_mode == 'interval':
            beat_interval = params.get('beat_interval', 1)
            return True, f"Added {total_cues_added} cues (every {beat_interval} beat{'s' if beat_interval > 1 else ''}) starting at {start_time:.1f}s"
        elif repeat_mode == 'duration':
            duration = params.get('duration_beats', params.get('duration_seconds', 8))
            unit = 'beats' if 'duration_beats' in params else 'seconds'
            return True, f"Added {total_cues_added} repeating cues for {duration} {unit} starting at {start_time:.1f}s"
        elif repeat_mode == 'continuous':
            return True, f"Added {total_cues_added} continuous effect cues starting at {start_time:.1f}s"
        else:
            return True, f"Added {total_cues_added} cues starting at {start_time:.1f}s"
    
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
        """Execute a modify cue command using replacement strategy."""
        
        print(f"🔍 Executing modify command:")
        print(f"   Time: {interpretation['time']}")
        print(f"   Fixtures: {interpretation['fixtures']}")
        print(f"   Preset: {interpretation['preset']}")
        print(f"   Parameters: {interpretation['parameters']}")
        
        if not interpretation['time']:
            return False, "Could not determine timing for the modification"
        
        if not interpretation['fixtures']:
            return False, "Could not identify which fixtures to modify"
        
        # Strategy: Replace existing cues with new ones
        # This effectively "modifies" by removing old and adding new
        
        modifications_made = 0
        time_tolerance = 0.5  # Allow 0.5 second tolerance for matching existing cues
        
        for fixture_id in interpretation['fixtures']:
            # Find existing cues near this time for this fixture
            existing_cues = []
            for cue in self.cue_manager.cue_list:
                if (cue.get('fixture') == fixture_id and 
                    abs(cue.get('time', 0) - interpretation['time']) <= time_tolerance):
                    existing_cues.append(cue)
            
            if existing_cues:
                # Remove existing cues first
                for old_cue in existing_cues:
                    try:
                        # Use the correct CueManager delete method
                        self.cue_manager.delete_cue(old_cue.get('fixture'), old_cue.get('time'))
                    except Exception as e:
                        print(f"   Warning: Could not delete cue: {e}")
                        # Fallback: remove from list directly
                        if old_cue in self.cue_manager.cue_list:
                            self.cue_manager.cue_list.remove(old_cue)
                
                print(f"   Removed {len(existing_cues)} existing cue(s) for {fixture_id}")
            
            # Add new cue with modified parameters
            if interpretation['preset']:
                new_cue = {
                    'time': interpretation['time'],
                    'fixture': fixture_id,
                    'preset': interpretation['preset'],
                    'parameters': interpretation['parameters']
                }
                self.cue_manager.add_cue(new_cue)
                modifications_made += 1
                print(f"   Added replacement cue for {fixture_id}")
        
        if modifications_made > 0:
            return True, f"Modified {modifications_made} cue(s) at {interpretation['time']:.1f}s - replaced with '{interpretation['preset']}' preset"
        else:
            # No existing cues found, treat as add command
            return self._execute_add_command(interpretation)
    
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
