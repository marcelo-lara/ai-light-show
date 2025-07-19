"""
Preset command parser for the Actions Parser Service.
"""

from typing import List
from backend.models.actions_sheet import ActionModel


class PresetCommandParser:
    """Parser for preset commands like '#preset moving_head Drop at 34.2s'"""
    
    def __init__(self, resolve_fixtures_func):
        """
        Initialize the preset command parser.
        
        Args:
            resolve_fixtures_func: Function to resolve fixture specifications
        """
        self.resolve_fixtures = resolve_fixtures_func
    
    def parse(self, match) -> List[ActionModel]:
        """Parse preset command regex match."""
        fixture_spec, preset_name, start_time = match.groups()
        
        # Resolve fixtures
        fixture_ids = self.resolve_fixtures(fixture_spec)
        
        # Parse timing
        start_time = float(start_time)
        
        actions = []
        for fixture_id in fixture_ids:
            action = ActionModel(
                action='preset',
                fixture_id=fixture_id,
                parameters={
                    'preset_name': preset_name
                },
                start_time=start_time,
                duration=0.1  # Instantaneous change
            )
            actions.append(action)
        
        return actions
