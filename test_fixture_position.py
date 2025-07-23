#!/usr/bin/env python3
"""Test script to verify fixture position property works correctly."""

import sys
import json
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.models.fixtures.fixture_model import FixtureModel

def test_fixture_position():
    """Test the fixture position property."""
    print("🏗️ Testing Fixture Position Property")
    print("=" * 50)
    
    # Load fixtures.json
    fixtures_file = Path(__file__).parent / "fixtures" / "fixtures.json"
    try:
        with open(fixtures_file, 'r') as f:
            fixtures_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Could not find fixtures.json at {fixtures_file}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing fixtures.json: {e}")
        return
    
    print(f"📋 Loaded {len(fixtures_data)} fixtures from fixtures.json\n")
    
    # Test each fixture
    for fixture_config in fixtures_data:
        fixture = FixtureModel(
            id=fixture_config['id'],
            name=fixture_config['name'],
            fixture_type=fixture_config['type'],
            channels=len(fixture_config.get('channels', {})),
            config=fixture_config
        )
        
        print(f"🔧 Testing fixture: {fixture.name} ({fixture.id})")
        
        # Test position property
        position = fixture.position
        if position:
            print(f"  📍 Position: x={position.x}, y={position.y}, z={position.z}, label='{position.label}'")
        else:
            print(f"  ⚠️ No position data found")
        
        print()

if __name__ == "__main__":
    test_fixture_position()
