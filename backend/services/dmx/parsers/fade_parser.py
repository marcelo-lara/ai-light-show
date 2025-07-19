"""
Fade command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class FadeCommandParser:
    """Parser for fade commands like 'fade head_el150 from red to blue at 10s for 3s'"""
    
    def __init__(self, resolve_fixtures_func, parse_colors_func):
        """
        Initialize the fade command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
            parse_colors_func: Function to parse color specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
        self.parse_colors = parse_colors_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse fade command regex match."""
        fixture_spec, from_colors_str, to_colors_str, start_time, duration = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse colors
        from_colors = self.parse_colors(from_colors_str) if from_colors_str else ['white']
        to_colors = self.parse_colors(to_colors_str) if to_colors_str else ['white']
        
        # Parse timing
        start_time = float(start_time)
        duration = float(duration) if duration else 2.0
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='fade',
                fixture_id=fixture_id,
                parameters={
                    'from_colors': from_colors,
                    'to_colors': to_colors
                },
                start_time=start_time,
                duration=duration
            )
            actions.append(action)
        
        return actions
