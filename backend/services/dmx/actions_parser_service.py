"""
Actions Parser Service

This service is responsible for parsing action commands from text input 
and converting them into structured actions for the ActionsSheet.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from backend.models.actions_sheet import ActionModel
from backend.models.fixtures.fixtures_list_model import FixturesListModel
from .parsers import FlashCommandParser, FadeCommandParser, StrobeCommandParser


class ActionsParserService:
    """
    Service for parsing natural language action commands into structured ActionModel objects.
    
    Supports parsing commands like:
    - "flash parcan_pl blue at 5.2s for 1.5s with intensity 0.8"
    - "fade head_el150 from red to blue at 10s for 3s"
    - "strobe all_parcans at 15s for 2s"
    """
    
    def __init__(self, fixtures: FixturesListModel, debug: bool = False):
        """
        Initialize the Actions Parser Service.
        
        Args:
            fixtures (FixturesListModel): The fixtures model to validate fixture IDs
            debug (bool): Enable debug output
        """
        self.fixtures = fixtures
        self.debug = debug
        
        # Color mapping for common color names
        self.color_map = {
            'red': 'red',
            'green': 'green', 
            'blue': 'blue',
            'white': ['red', 'green', 'blue'],
            'yellow': ['red', 'green'],
            'cyan': ['green', 'blue'],
            'magenta': ['red', 'blue'],
            'purple': ['red', 'blue'],
            'orange': ['red', 'green'],  # More red than green
            'pink': ['red', 'blue'],
        }
        
        # Fixture group aliases
        self.fixture_groups = {
            'all': list(self.fixtures.fixtures.keys()),
            'all_parcans': [fid for fid, f in self.fixtures.fixtures.items() if 'parcan' in f.fixture_type],
            'all_heads': [fid for fid, f in self.fixtures.fixtures.items() if 'head' in f.fixture_type or 'moving' in f.fixture_type],
            'rgb_lights': [fid for fid, f in self.fixtures.fixtures.items() if f.fixture_type in ['parcan', 'rgb']],
        }
        
        # Initialize command parsers
        self.flash_parser = FlashCommandParser(self._resolve_fixtures, self._parse_colors)
        self.fade_parser = FadeCommandParser(self._resolve_fixtures, self._parse_colors)
        self.strobe_parser = StrobeCommandParser(self._resolve_fixtures)
    
    def parse_command(self, command: str) -> List[ActionModel]:
        """
        Parse a single action command into ActionModel objects.
        
        Args:
            command (str): Natural language command
            
        Returns:
            List[ActionModel]: List of parsed actions (may be multiple for fixture groups)
        """
        if self.debug:
            print(f"🔍 Parsing command: '{command}'")
        
        # Clean and normalize the command
        command = command.strip().lower()
        if not command:
            return []
        
        # Try different parsing patterns
        actions = []
        
        # Pattern 1: Basic flash command
        # "flash parcan_pl blue at 5.2s for 1.5s with intensity 0.8"
        flash_match = re.match(
            r'flash\s+(\w+)\s*(?:([\w,\s]+))?\s*at\s+([\d.]+)s?\s*(?:for\s+([\d.]+)s?)?\s*(?:with\s+intensity\s+([\d.]+))?',
            command
        )
        if flash_match:
            actions.extend(self.flash_parser.parse(flash_match))
        
        # Pattern 2: Fade command
        # "fade head_el150 from red to blue at 10s for 3s"
        fade_match = re.match(
            r'fade\s+(\w+)\s*(?:from\s+([\w,\s]+)\s+to\s+([\w,\s]+))?\s*at\s+([\d.]+)s?\s*(?:for\s+([\d.]+)s?)?',
            command
        )
        if fade_match:
            actions.extend(self.fade_parser.parse(fade_match))
        
        # Pattern 3: Strobe command
        # "strobe all_parcans at 15s for 2s"
        strobe_match = re.match(
            r'strobe\s+(\w+)\s*at\s+([\d.]+)s?\s*(?:for\s+([\d.]+)s?)?',
            command
        )
        if strobe_match:
            actions.extend(self.strobe_parser.parse(strobe_match))
        
        # Pattern 4: Generic action with parameters
        # "action_name fixture_id param1=value1 param2=value2 at 5s for 2s"
        generic_match = re.match(
            r'(\w+)\s+(\w+)\s*(.*?)\s*at\s+([\d.]+)s?\s*(?:for\s+([\d.]+)s?)?',
            command
        )
        if not actions and generic_match:
            actions.extend(self._parse_generic_command(generic_match))
        
        if self.debug:
            print(f"  ✅ Parsed {len(actions)} action(s)")
            for action in actions:
                print(f"    - {action.action} on {action.fixture_id} at {action.start_time}s")
        
        return actions
    
    def parse_commands(self, commands: List[str]) -> List[ActionModel]:
        """
        Parse multiple action commands.
        
        Args:
            commands (List[str]): List of natural language commands
            
        Returns:
            List[ActionModel]: List of all parsed actions
        """
        all_actions = []
        for command in commands:
            actions = self.parse_command(command)
            all_actions.extend(actions)
        return all_actions
    
    def _parse_generic_command(self, match) -> List[ActionModel]:
        """Parse generic action command."""
        action_name, fixture_spec, params_str, start_time, duration = match.groups()
        
        # Resolve fixtures
        fixture_ids = self._resolve_fixtures(fixture_spec)
        
        # Parse parameters
        parameters = self._parse_parameters(params_str) if params_str else {}
        
        # Parse timing
        start_time = float(start_time)
        duration = float(duration) if duration else 1.0
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action=action_name,
                fixture_id=fixture_id,
                parameters=parameters,
                start_time=start_time,
                duration=duration
            )
            actions.append(action)
        
        return actions
    
    def _resolve_fixtures(self, fixture_spec: str) -> List[str]:
        """
        Resolve fixture specification to actual fixture IDs.
        
        Args:
            fixture_spec (str): Fixture ID or group name
            
        Returns:
            List[str]: List of fixture IDs
        """
        fixture_spec = fixture_spec.strip()
        
        # Check if it's a group
        if fixture_spec in self.fixture_groups:
            return self.fixture_groups[fixture_spec]
        
        # Check if it's a direct fixture ID
        if fixture_spec in self.fixtures.fixtures:
            return [fixture_spec]
        
        # Check for partial matches
        matches = [fid for fid in self.fixtures.fixtures.keys() if fixture_spec in fid]
        if matches:
            return matches
        
        if self.debug:
            print(f"    ⚠️  Unknown fixture: '{fixture_spec}'")
        return []
    
    def _parse_colors(self, colors_str: str) -> List[str]:
        """
        Parse color specification.
        
        Args:
            colors_str (str): Color specification like "red", "blue,green", etc.
            
        Returns:
            List[str]: List of color names
        """
        if not colors_str:
            return ['white']
        
        colors = []
        color_parts = [c.strip() for c in colors_str.split(',')]
        
        for color_part in color_parts:
            if color_part in self.color_map:
                color_value = self.color_map[color_part]
                if isinstance(color_value, list):
                    colors.extend(color_value)
                else:
                    colors.append(color_value)
            else:
                colors.append(color_part)  # Use as-is if not in map
        
        return colors
    
    def _parse_parameters(self, params_str: str) -> Dict[str, Any]:
        """
        Parse parameter string like "intensity=0.8 speed=fast".
        
        Args:
            params_str (str): Parameter string
            
        Returns:
            Dict[str, Any]: Parameters dictionary
        """
        parameters = {}
        if not params_str:
            return parameters
        
        # Look for key=value pairs
        param_matches = re.findall(r'(\w+)=([^\s]+)', params_str)
        for key, value in param_matches:
            # Try to convert to appropriate type
            try:
                # Try float first
                if '.' in value:
                    parameters[key] = float(value)
                else:
                    parameters[key] = int(value)
            except ValueError:
                # Keep as string if not numeric
                parameters[key] = value
        
        return parameters
    
    def validate_action(self, action: ActionModel) -> Tuple[bool, List[str]]:
        """
        Validate a parsed action.
        
        Args:
            action (ActionModel): Action to validate
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_issues)
        """
        issues = []
        
        # Check if fixture exists
        if action.fixture_id not in self.fixtures.fixtures:
            issues.append(f"Fixture '{action.fixture_id}' not found")
        
        # Check if action is supported by fixture
        elif action.action not in self.fixtures.fixtures[action.fixture_id].actions:
            available_actions = self.fixtures.fixtures[action.fixture_id].actions
            issues.append(f"Action '{action.action}' not supported by '{action.fixture_id}'. Available: {available_actions}")
        
        # Check timing
        if action.start_time < 0:
            issues.append("Start time cannot be negative")
        
        if action.duration <= 0:
            issues.append("Duration must be positive")
        
        return len(issues) == 0, issues
    
    def get_supported_commands_help(self) -> str:
        """
        Get help text for supported command formats.
        
        Returns:
            str: Help text
        """
        help_text = """
Supported Action Command Formats:

1. Flash Commands:
   flash <fixture> [color] at <time>s [for <duration>s] [with intensity <value>]
   Examples:
   - flash parcan_pl blue at 5.2s for 1.5s with intensity 0.8
   - flash all_parcans red at 10s
   
2. Fade Commands:
   fade <fixture> from <color> to <color> at <time>s [for <duration>s]
   Examples:
   - fade head_el150 from red to blue at 10s for 3s
   - fade all at 5s
   
3. Strobe Commands:
   strobe <fixture> at <time>s [for <duration>s]
   Examples:
   - strobe all_parcans at 15s for 2s
   - strobe parcan_pl at 8s
   
4. Generic Commands:
   <action> <fixture> [param=value ...] at <time>s [for <duration>s]
   Examples:
   - full parcan_pl intensity=0.5 at 3s for 2s

Fixture Groups:
- all: All fixtures
- all_parcans: All parcan fixtures
- all_heads: All moving head fixtures
- rgb_lights: All RGB capable fixtures

Colors: red, green, blue, white, yellow, cyan, magenta, purple, orange, pink
"""
        return help_text

