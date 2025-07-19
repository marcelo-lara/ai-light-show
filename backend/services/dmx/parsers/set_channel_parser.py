"""
Set channel command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class SetChannelCommandParser:
    """Parser for set channel commands like '#set parcan_l red channel to 0.5 at 12.23s'"""
    
    def __init__(self, resolve_fixtures_func):
        """
        Initialize the set channel command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse set channel command regex match."""
        fixture_spec, channel_name, value, start_time = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse timing and value (normalized 0.0-1.0)
        start_time = float(start_time)
        channel_value = float(value)
        
        # Ensure value is normalized between 0.0 and 1.0
        if channel_value < 0.0:
            channel_value = 0.0
        elif channel_value > 1.0:
            channel_value = 1.0
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='set_channel',
                fixture_id=fixture_id,
                parameters={
                    'channel': channel_name,
                    'value': channel_value
                },
                start_time=start_time,
                duration=0.1  # Instantaneous change
            )
            actions.append(action)
        
        return actions
