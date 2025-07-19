"""
Strobe channel command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class StrobeChannelCommandParser:
    """Parser for strobe channel commands like '#strobe parcan_l white channel rate 10 duration 2s'"""
    
    def __init__(self, resolve_fixtures_func):
        """
        Initialize the strobe channel command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse strobe channel command regex match."""
        fixture_spec, channel_name, frequency, duration = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse frequency and duration
        strobe_rate = float(frequency)  # Hz
        strobe_duration = float(duration)  # seconds
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='strobe_channel',
                fixture_id=fixture_id,
                parameters={
                    'channel': channel_name,
                    'frequency': strobe_rate
                },
                start_time=0.0,  # Start immediately when triggered
                duration=strobe_duration
            )
            actions.append(action)
        
        return actions
