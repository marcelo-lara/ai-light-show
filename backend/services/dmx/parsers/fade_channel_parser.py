"""
Fade channel command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class FadeChannelCommandParser:
    """Parser for fade channel commands like '#fade parcan_l red channel from 0.0 to 1.0 duration 5s'"""
    
    def __init__(self, resolve_fixtures_func):
        """
        Initialize the fade channel command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse fade channel command regex match."""
        fixture_spec, channel_name, start_value, end_value, duration = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse values and duration (normalized 0.0-1.0)
        start_val = float(start_value)
        end_val = float(end_value)
        fade_duration = float(duration)
        
        # Ensure values are normalized between 0.0 and 1.0
        start_val = max(0.0, min(1.0, start_val))
        end_val = max(0.0, min(1.0, end_val))
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='fade_channel',
                fixture_id=fixture_id,
                parameters={
                    'channel': channel_name,
                    'start_value': start_val,
                    'end_value': end_val
                },
                start_time=0.0,  # Start immediately when triggered
                duration=fade_duration
            )
            actions.append(action)
        
        return actions
