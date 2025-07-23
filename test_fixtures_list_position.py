#!/usr/bin/env python3
"""Test script to verify fixtures list loads position data correctly."""

import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent / "backend"))

from backend.models.fixtures.fixtures_list_model import FixturesListModel
from backend.services.dmx.dmx_canvas import DmxCanvas

def test_fixtures_list_position():
    """Test that FixturesListModel loads position data correctly."""
    print("🏗️ Testing Fixtures List Position Loading")
    print("=" * 50)
    
    # Create a DMX canvas
    dmx_canvas = DmxCanvas(fps=30, duration=10.0)
    
    # Load fixtures with debug enabled
    fixtures_file = Path(__file__).parent / "fixtures" / "fixtures.json"
    
    try:
        fixtures_list = FixturesListModel(
            fixtures_config_file=fixtures_file,
            dmx_canvas=dmx_canvas,
            debug=True  # Enable debug output
        )
        
        print(f"\n📋 Successfully loaded fixtures list")
        print(f"📍 Testing individual fixture positions:")
        
        # Test each fixture's position individually
        for fixture_id, fixture in fixtures_list.fixtures.items():
            position = fixture.position
            if position:
                print(f"  ✅ {fixture.name}: x={position.x}, y={position.y}, z={position.z}, label='{position.label}'")
            else:
                print(f"  ❌ {fixture.name}: No position data")
        
        # Test accessing fixtures by specific IDs
        print(f"\n🎯 Testing specific fixture access:")
        
        head_fixture = fixtures_list.get_fixture("head_el150")
        if head_fixture and head_fixture.position:
            pos = head_fixture.position
            print(f"  🎭 Moving Head: {pos.label} at ({pos.x}, {pos.y}, {pos.z})")
        
        parcan_l = fixtures_list.get_fixture("parcan_l")
        if parcan_l and parcan_l.position:
            pos = parcan_l.position
            print(f"  💡 ParCan L: {pos.label} at ({pos.x}, {pos.y}, {pos.z})")
        
        # Test position-based queries
        print(f"\n📍 Testing position-based queries:")
        
        # Get fixtures by position label
        stage_left_fixtures = fixtures_list.get_fixtures_by_position_label("stage_left")
        print(f"  📍 Fixtures at 'stage_left': {[f.name for f in stage_left_fixtures]}")
        
        stage_right_fixtures = fixtures_list.get_fixtures_by_position_label("stage_right")
        print(f"  📍 Fixtures at 'stage_right': {[f.name for f in stage_right_fixtures]}")
        
        # Get fixtures in specific area (left side of stage)
        left_area_fixtures = fixtures_list.get_fixtures_in_area(min_x=0.0, max_x=0.5, min_y=0.0, max_y=1.0)
        print(f"  🔲 Fixtures in left area (x: 0.0-0.5): {[f.name for f in left_area_fixtures]}")
        
        # Get fixtures in specific area (front of stage)
        front_area_fixtures = fixtures_list.get_fixtures_in_area(min_x=0.0, max_x=1.0, min_y=0.0, max_y=0.5)
        print(f"  🔲 Fixtures in front area (y: 0.0-0.5): {[f.name for f in front_area_fixtures]}")
            
    except Exception as e:
        print(f"❌ Error loading fixtures: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fixtures_list_position()
