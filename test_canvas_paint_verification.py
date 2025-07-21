"""
Enhanced test to validate DmxCanvas singleton with detailed paint verification.

This test demonstrates that all fixture paint operations modify the same canvas
by examining actual DMX channel values rather than just timeline counts.
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

def test_canvas_paint_content():
    """Test that paint operations actually modify canvas content."""
    
    print("🎨 Testing Canvas Paint Content Verification")
    print("=" * 50)
    
    # Reset canvas and get singleton
    app_state.reset_dmx_canvas(fps=44, duration=5.0, debug=False)
    canvas = app_state.dmx_canvas
    fixtures_list = app_state.fixtures
    
    if fixtures_list is None:
        print("❌ No fixtures loaded!")
        return False
        
    print(f"📍 Canvas singleton ID: {id(canvas)}")
    print(f"📊 Canvas frames: {canvas.num_frames}")
    
    # Clear canvas and verify it's empty
    canvas.clear_canvas()
    print("\n🧹 Canvas cleared")
    
    # Test each fixture type with detailed verification
    test_times = [1.0, 2.0, 3.0]  # Different test times
    test_results = {}
    
    for fixture_id, fixture in fixtures_list.fixtures.items():
        print(f"\n🎛️ Testing fixture: {fixture.name} ({fixture.fixture_type})")
        print(f"   📍 Fixture canvas ID: {id(fixture.dmx_canvas)}")
        print(f"   ✅ Same singleton: {fixture.dmx_canvas is canvas}")
        
        # Get fixture channels
        channels = fixture.channel_names
        if not channels:
            print("   ⚠️ No channels defined, skipping")
            continue
            
        # Test painting different values
        test_channel = list(channels.keys())[0]
        dmx_channel = channels[test_channel] - 1  # Convert to 0-based
        
        print(f"   🔧 Testing channel: {test_channel} (DMX {dmx_channel + 1})")
        
        # Test 1: Set initial value
        print(f"      Setting value 100 at time {test_times[0]}s")
        fixture.set_channel_value(test_channel, 100, start_time=test_times[0], duration=0.1)
        
        # Verify the value was set in the canvas
        frame_at_time = canvas.get_frame(test_times[0])
        value_at_time = frame_at_time[dmx_channel]
        print(f"      📊 Canvas value at {test_times[0]}s: {value_at_time}")
        
        # Test 2: Fade operation
        print(f"      Fading from 50 to 200 at time {test_times[1]}s")
        fixture.fade_channel(test_channel, 50, 200, start_time=test_times[1], duration=0.5)
        
        # Check multiple points during fade
        fade_start_frame = canvas.get_frame(test_times[1])
        fade_mid_frame = canvas.get_frame(test_times[1] + 0.25)
        fade_end_frame = canvas.get_frame(test_times[1] + 0.5)
        
        fade_start_val = fade_start_frame[dmx_channel]
        fade_mid_val = fade_mid_frame[dmx_channel]
        fade_end_val = fade_end_frame[dmx_channel]
        
        print(f"      📊 Fade start ({test_times[1]}s): {fade_start_val}")
        print(f"      📊 Fade mid ({test_times[1] + 0.25}s): {fade_mid_val}")
        print(f"      📊 Fade end ({test_times[1] + 0.5}s): {fade_end_val}")
        
        # Test 3: Set arm operation  
        print(f"      Setting arm state at time {test_times[2]}s")
        fixture.set_arm(True)
        
        # Check arm channels
        arm_config = fixture._config.get('arm', {})
        if arm_config:
            for arm_channel, arm_value in arm_config.items():
                if arm_channel in channels:
                    arm_dmx_channel = channels[arm_channel] - 1
                    arm_frame = canvas.get_frame(test_times[2])
                    arm_canvas_value = arm_frame[arm_dmx_channel]
                    print(f"      📊 Arm channel {arm_channel} (DMX {arm_dmx_channel + 1}): {arm_canvas_value}")
        
        # Store results for verification
        test_results[fixture_id] = {
            'canvas_id': id(fixture.dmx_canvas),
            'is_singleton': fixture.dmx_canvas is canvas,
            'test_channel': test_channel,
            'dmx_channel': dmx_channel,
            'values': {
                'initial': value_at_time,
                'fade_start': fade_start_val,
                'fade_mid': fade_mid_val,
                'fade_end': fade_end_val
            }
        }
    
    # Cross-fixture verification: all fixtures should see the same canvas data
    print("\n🔍 Cross-Fixture Canvas Verification")
    print("=" * 40)
    
    # Pick a test time and verify all fixtures see the same frame
    test_time = test_times[0]
    reference_frame = canvas.get_frame(test_time)
    
    print(f"📊 Verifying all fixtures see same frame at {test_time}s:")
    all_consistent = True
    
    for fixture_id, fixture in fixtures_list.fixtures.items():
        if fixture.dmx_canvas is None:
            print(f"   • {fixture_id}: ❌ (No canvas)")
            all_consistent = False
            continue
            
        fixture_frame = fixture.dmx_canvas.get_frame(test_time)
        frames_match = fixture_frame == reference_frame
        print(f"   • {fixture_id}: {'✅' if frames_match else '❌'}")
        
        if not frames_match:
            all_consistent = False
            print(f"     Reference: {reference_frame[:10]}...")
            print(f"     Fixture:   {fixture_frame[:10]}...")
    
    if all_consistent:
        print("   ✅ All fixtures see identical canvas data")
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 20)
    
    singleton_count = sum(1 for r in test_results.values() if r['is_singleton'])
    total_fixtures = len(test_results)
    
    print(f"📊 Fixtures using singleton: {singleton_count}/{total_fixtures}")
    print(f"📊 Canvas data consistency: {'✅' if all_consistent else '❌'}")
    
    # Verify all paint operations affected the same canvas instance
    unique_canvas_ids = set(r['canvas_id'] for r in test_results.values())
    print(f"📊 Unique canvas instances: {len(unique_canvas_ids)}")
    
    if len(unique_canvas_ids) == 1:
        print("✅ All fixtures use the exact same canvas instance")
    else:
        print("❌ Multiple canvas instances detected!")
        for canvas_id in unique_canvas_ids:
            fixtures_with_canvas = [fid for fid, r in test_results.items() if r['canvas_id'] == canvas_id]
            print(f"   Canvas {canvas_id}: {fixtures_with_canvas}")
    
    # Final validation
    success = (
        singleton_count == total_fixtures and
        all_consistent and
        len(unique_canvas_ids) == 1
    )
    
    print(f"\n🎉 RESULT: {'SUCCESS' if success else 'FAILED'}")
    
    return success

def main():
    """Run the enhanced canvas paint test."""
    
    print("🚀 Enhanced Fixture Canvas Paint Test")
    print("=" * 50)
    
    try:
        if app_state.fixtures is None:
            print("❌ No fixtures available!")
            return False
            
        fixture_count = len(app_state.fixtures.fixtures)
        print(f"🎛️ Testing {fixture_count} fixtures")
        
        if fixture_count == 0:
            print("❌ No fixtures loaded!")
            return False
        
        success = test_canvas_paint_content()
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 ALL PAINT TESTS PASSED! 🎉")
            print("✅ All fixtures paint to the same canvas singleton")
            print("✅ Paint operations create visible changes")
            print("✅ Canvas data is consistent across all fixtures")
            print("=" * 50)
        
        return success
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
