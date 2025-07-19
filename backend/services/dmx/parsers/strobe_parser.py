"""
Strobe command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class StrobeCommandParser:
    """Parser for strobe commands like 'strobe all_parcans at 15s for 2s'"""
    
    def __init__(self, resolve_fixtures_func):
        """
        Initialize the strobe command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse strobe command regex match."""
        fixture_spec, start_time, duration = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse timing
        start_time = float(start_time)
        duration = float(duration) if duration else 1.0
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='strobe',
                fixture_id=fixture_id,
                parameters={},
                start_time=start_time,
                duration=duration
            )
            actions.append(action)
        
        return actions
