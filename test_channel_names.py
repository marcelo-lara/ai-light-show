#!/usr/bin/env python3
"""
Quick test to verify channel_names property works correctly.
"""

from backend.config import FIXTURES_FILE
from backend.models.fixtures import FixturesListModel
from backend.services.dmx_canvas import DmxCanvas

# Initialize DMX Canvas
dmx_canvas = DmxCanvas(duration=10.0, debug=True)

# Initialize fixtures
fixtures = FixturesListModel(
    fixtures_config_file=FIXTURES_FILE,
    dmx_canvas=dmx_canvas,
    debug=True
)

# Test channel_names property
print("Testing channel_names property:")
for fixture_id, fixture in fixtures.fixtures.items():
    print(f"\n{fixture.name} ({fixture.id}) - Type: {fixture.fixture_type}")
    print(f"  Channel names: {fixture.channel_names}")
    print(f"  Available actions: {fixture.actions}")
    
    # Test if dim channel exists for flash
    if 'dim' in fixture.channel_names:
        print(f"  ✅ Has 'dim' channel at DMX {fixture.channel_names['dim']}")
    else:
        print(f"  ❌ No 'dim' channel found")
