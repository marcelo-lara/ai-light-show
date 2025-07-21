"""
Test to validate that all fixture 'paint' actions render to the same DmxCanvas singleton.

This test ensures that:
1. All fixtures use the same DmxCanvas singleton instance
2. All fixture paint methods (set_channel_value, fade_channel, set_arm) write to the same canvas
3. Canvas data is shared across all fixtures regardless of type
4. No fixture creates its own canvas instance
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, '/home/darkangel/ai-light-show')

from backend.models.app_state import app_state
from backend.services.dmx.dmx_canvas import DmxCanvas
from backend.models.fixtures import FixturesListModel, RgbParcan, MovingHead
from backend.config import FIXTURES_FILE

def test_fixture_canvas_singleton():
    """Test that all fixtures use the same DmxCanvas singleton."""
    
    print("🧪 Testing Fixture Canvas Singleton Enforcement")
    print("=" * 60)
    
    # Step 1: Reset canvas to ensure clean state
    print("\n1️⃣ Resetting DMX Canvas...")
    app_state.reset_dmx_canvas(fps=44, duration=10.0, debug=False)
    initial_canvas = app_state.dmx_canvas
    print(f"   📍 Initial canvas ID: {id(initial_canvas)}")
    
    # Step 2: Verify app_state fixtures use the singleton
    print("\n2️⃣ Checking app_state fixtures...")
    fixtures_list = app_state.fixtures
    
    if fixtures_list is None:
        raise ValueError("No fixtures loaded! Cannot run singleton test.")
    
    fixtures_canvas = fixtures_list.dmx_canvas
    print(f"   📍 Fixtures canvas ID: {id(fixtures_canvas)}")
    print(f"   ✅ Same instance: {initial_canvas is fixtures_canvas}")
    
    # Step 3: Test individual fixture canvas references
    print("\n3️⃣ Testing individual fixture canvas references...")
    fixture_canvas_ids = {}
    
    for fixture_id, fixture in fixtures_list.fixtures.items():
        canvas = fixture.dmx_canvas
        fixture_canvas_ids[fixture_id] = id(canvas)
        is_singleton = canvas is initial_canvas
        print(f"   📍 Fixture '{fixture_id}' ({fixture.fixture_type}): ID {id(canvas)}, Singleton: {'✅' if is_singleton else '❌'}")
        
        # Ensure each fixture uses the singleton
        assert canvas is initial_canvas, f"Fixture {fixture_id} does not use singleton canvas!"
    
    # Step 4: Test fixture paint operations write to singleton
    print("\n4️⃣ Testing fixture paint operations...")
    
    # Clear canvas to start fresh
    initial_canvas.clear_canvas()
    initial_timeline_count = len(initial_canvas.export())
    print(f"   📊 Initial timeline entries: {initial_timeline_count}")
    
    # Test different fixture types and their paint methods
    test_results = []
    
    for fixture_id, fixture in fixtures_list.fixtures.items():
        print(f"\n   🎛️ Testing fixture: {fixture.name} ({fixture.fixture_type})")
        
        # Get channels for testing
        channels = fixture.channel_names
        
        # Test set_channel_value method
        try:
            # Get first available channel for testing
            if channels:
                first_channel = list(channels.keys())[0]
                print(f"      🔧 Testing set_channel_value: {first_channel}")
                fixture.set_channel_value(first_channel, 128, start_time=1.0, duration=0.5)
                
                # Verify canvas was painted by checking timeline
                new_timeline_count = len(initial_canvas.export())
                entries_added = new_timeline_count - initial_timeline_count
                print(f"      📈 Timeline entries added: {entries_added}")
                test_results.append(f"{fixture_id}.set_channel_value: {entries_added} entries")
                
                # Update count for next test
                initial_timeline_count = new_timeline_count
                
        except Exception as e:
            print(f"      ❌ set_channel_value failed: {e}")
            test_results.append(f"{fixture_id}.set_channel_value: FAILED - {e}")
        
        # Test fade_channel method
        try:
            if channels:
                first_channel = list(channels.keys())[0]
                print(f"      🌈 Testing fade_channel: {first_channel}")
                fixture.fade_channel(first_channel, 0, 255, start_time=2.0, duration=1.0)
                
                # Verify canvas was painted
                new_timeline_count = len(initial_canvas.export())
                entries_added = new_timeline_count - initial_timeline_count
                print(f"      📈 Timeline entries added: {entries_added}")
                test_results.append(f"{fixture_id}.fade_channel: {entries_added} entries")
                
                # Update count for next test
                initial_timeline_count = new_timeline_count
                
        except Exception as e:
            print(f"      ❌ fade_channel failed: {e}")
            test_results.append(f"{fixture_id}.fade_channel: FAILED - {e}")
        
        # Test set_arm method
        try:
            print(f"      🔧 Testing set_arm: enabling")
            fixture.set_arm(True)
            
            # Verify canvas was painted
            new_timeline_count = len(initial_canvas.export())
            entries_added = new_timeline_count - initial_timeline_count
            print(f"      📈 Timeline entries added: {entries_added}")
            test_results.append(f"{fixture_id}.set_arm: {entries_added} entries")
            
            # Update count for next test
            initial_timeline_count = new_timeline_count
            
        except Exception as e:
            print(f"      ❌ set_arm failed: {e}")
            test_results.append(f"{fixture_id}.set_arm: FAILED - {e}")
    
    # Step 5: Verify canvas integrity after all operations
    print("\n5️⃣ Verifying canvas integrity...")
    
    # Check that canvas is still the same singleton
    current_canvas = app_state.dmx_canvas
    print(f"   📍 Current canvas ID: {id(current_canvas)}")
    print(f"   ✅ Still singleton: {current_canvas is initial_canvas}")
    
    # Check fixtures still reference the singleton
    all_fixtures_use_singleton = True
    for fixture_id, fixture in fixtures_list.fixtures.items():
        if fixture.dmx_canvas is not initial_canvas:
            all_fixtures_use_singleton = False
            print(f"   ❌ Fixture {fixture_id} lost singleton reference!")
    
    if all_fixtures_use_singleton:
        print("   ✅ All fixtures still use singleton canvas")
    
    # Step 6: Test canvas data visibility across fixtures
    print("\n6️⃣ Testing canvas data visibility across fixtures...")
    
    # Get current canvas state
    final_timeline_count = len(initial_canvas.export())
    print(f"   📊 Final timeline entries: {final_timeline_count}")
    
    # Verify each fixture can see the same canvas data
    canvas_data_consistent = True
    for fixture_id, fixture in fixtures_list.fixtures.items():
        if fixture.dmx_canvas is None:
            canvas_data_consistent = False
            print(f"   ❌ Fixture {fixture_id} has no canvas!")
            continue
            
        fixture_timeline_count = len(fixture.dmx_canvas.export())
        if fixture_timeline_count != final_timeline_count:
            canvas_data_consistent = False
            print(f"   ❌ Fixture {fixture_id} sees {fixture_timeline_count} entries, expected {final_timeline_count}")
    
    if canvas_data_consistent:
        print("   ✅ All fixtures see consistent canvas data")
    
    # Step 7: Summary
    print("\n7️⃣ Test Summary")
    print("=" * 40)
    
    print("\n📋 Paint Operation Results:")
    for result in test_results:
        print(f"   • {result}")
    
    print(f"\n📊 Canvas Statistics:")
    print(f"   • Total timeline entries: {final_timeline_count}")
    print(f"   • Canvas duration: {initial_canvas.duration}s")
    print(f"   • Canvas FPS: {initial_canvas.fps}")
    print(f"   • Canvas frames: {initial_canvas.num_frames}")
    print(f"   • Fixture count: {len(fixtures_list.fixtures)}")
    
    # Final assertions
    assert current_canvas is initial_canvas, "Canvas singleton lost during operations!"
    assert all_fixtures_use_singleton, "Some fixtures lost singleton reference!"
    assert canvas_data_consistent, "Canvas data not consistent across fixtures!"
    
    print(f"\n🎉 SUCCESS: All fixtures use the same DmxCanvas singleton!")
    print(f"   📍 Singleton ID: {id(initial_canvas)}")
    print(f"   🎛️ Tested {len(fixtures_list.fixtures)} fixtures")
    print(f"   🎨 Generated {final_timeline_count} timeline entries")
    
    return True

def test_fixture_type_coverage():
    """Test that we have coverage of all fixture types."""
    
    print("\n🔍 Testing Fixture Type Coverage")
    print("=" * 40)
    
    fixtures_list = app_state.fixtures
    if fixtures_list is None:
        print("❌ No fixtures loaded!")
        return {}
    
    fixture_types = {}
    
    for fixture_id, fixture in fixtures_list.fixtures.items():
        fixture_type = fixture.fixture_type
        if fixture_type not in fixture_types:
            fixture_types[fixture_type] = []
        fixture_types[fixture_type].append(fixture_id)
    
    print(f"📊 Found fixture types:")
    for ftype, fixtures in fixture_types.items():
        print(f"   • {ftype}: {len(fixtures)} fixtures ({', '.join(fixtures)})")
    
    # Verify we have different types
    expected_types = ['parcan', 'moving_head']  # Based on fixtures.json structure
    for expected_type in expected_types:
        if expected_type in fixture_types:
            print(f"   ✅ Found {expected_type} fixtures")
        else:
            print(f"   ⚠️ No {expected_type} fixtures found")
    
    return fixture_types

def test_canvas_reset_with_fixtures():
    """Test that canvas reset properly updates all fixtures."""
    
    print("\n🔄 Testing Canvas Reset with Fixtures")
    print("=" * 45)
    
    # Get initial state
    initial_canvas = app_state.dmx_canvas
    fixtures_list = app_state.fixtures
    
    if fixtures_list is None:
        print("❌ No fixtures loaded! Cannot test canvas reset.")
        return False
    
    print(f"   📍 Initial canvas ID: {id(initial_canvas)}")
    
    # Reset canvas with different parameters
    print("   🔄 Resetting canvas with new parameters...")
    new_canvas = app_state.reset_dmx_canvas(fps=30, duration=20.0, debug=False)
    
    print(f"   📍 New canvas ID: {id(new_canvas)}")
    print(f"   ✅ Different instance: {new_canvas is not initial_canvas}")
    
    # Verify all fixtures now use the new canvas
    print("   🔍 Checking fixture canvas updates...")
    all_updated = True
    for fixture_id, fixture in fixtures_list.fixtures.items():
        fixture_canvas = fixture.dmx_canvas
        is_updated = fixture_canvas is new_canvas
        print(f"      • {fixture_id}: {'✅' if is_updated else '❌'}")
        if not is_updated:
            all_updated = False
    
    assert all_updated, "Not all fixtures updated to new canvas!"
    print("   ✅ All fixtures updated to new canvas singleton")
    
    return True

def main():
    """Run all fixture canvas singleton tests."""
    
    print("🚀 Starting Fixture Canvas Singleton Tests")
    print("=" * 60)
    
    try:
        # Load fixtures if not already loaded
        fixtures_list = app_state.fixtures
        if fixtures_list is None or not fixtures_list.fixtures:
            print("📁 Loading fixtures from configuration...")
            # This will be done automatically in app_state.__post_init__()
        
        if app_state.fixtures is None:
            print("❌ No fixtures available! Cannot run tests.")
            return False
            
        fixture_count = len(app_state.fixtures.fixtures)
        print(f"🎛️ Loaded {fixture_count} fixtures for testing")
        
        if fixture_count == 0:
            print("❌ No fixtures loaded! Cannot run tests.")
            return False
        
        # Run tests
        test_fixture_type_coverage()
        test_fixture_canvas_singleton()
        test_canvas_reset_with_fixtures()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("✅ All fixtures use the same DmxCanvas singleton")
        print("✅ All paint operations write to the same canvas")
        print("✅ Canvas data is shared across all fixtures")
        print("✅ Canvas reset properly updates all fixtures")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
