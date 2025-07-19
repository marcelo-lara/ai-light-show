"""
Flash command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class FlashCommandParser:
    """Parser for flash commands like 'flash parcan_pl blue at 5.2s for 1.5s with intensity 0.8'"""
    
    def __init__(self, resolve_fixtures_func, parse_colors_func):
        """
        Initialize the flash command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
            parse_colors_func: Function to parse color specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
        self.parse_colors = parse_colors_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse flash command regex match."""
        fixture_spec, colors_str, start_time, duration, intensity = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse colors
        colors = self.parse_colors(colors_str) if colors_str else ['white']
        
        # Parse timing and intensity
        start_time = float(start_time)
        duration = float(duration) if duration else 1.0
        intensity = float(intensity) if intensity else 1.0
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='flash',
                fixture_id=fixture_id,
                parameters={
                    'colors': colors,
                    'intensity': intensity
                },
                start_time=start_time,
                duration=duration
            )
            actions.append(action)
        
        return actions
