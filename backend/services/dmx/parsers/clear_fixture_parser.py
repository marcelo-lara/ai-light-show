"""
Clear fixture state command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class ClearFixtureCommandParser:
    """Parser for clear fixture commands like '#clear parcan_l state at 15.0s'"""
    
    def __init__(self, resolve_fixtures_func):
        """
        Initialize the clear fixture command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse clear fixture command regex match."""
        fixture_spec, start_time = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse timing
        clear_time = float(start_time)
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='clear_state',
                fixture_id=fixture_id,
                parameters={},
                start_time=clear_time,
                duration=0.1  # Instantaneous change
            )
            actions.append(action)
        
        return actions
