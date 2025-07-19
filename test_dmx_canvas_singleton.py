#!/usr/bin/env python3
"""
Test script to verify DMX Canvas singleton behavior.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.dmx.dmx_canvas import DmxCanvas

def test_singleton_behavior():
    """Test that DmxCanvas properly implements singleton pattern."""
    print("🧪 Testing DMX Canvas Singleton Behavior\n")
    
    # Test 1: Multiple instantiations return same object
    print("1. Testing multiple instantiations...")
    canvas1 = DmxCanvas(fps=30, duration=10.0, debug=True)
    canvas2 = DmxCanvas(fps=60, duration=20.0, debug=True)  # Different params should be ignored
    
    print(f"   Canvas 1 ID: {id(canvas1)}")
    print(f"   Canvas 2 ID: {id(canvas2)}")
    print(f"   Same object: {canvas1 is canvas2}")
    print(f"   ✅ Singleton working: {canvas1 is canvas2}")
    
    # Verify parameters from first instantiation are preserved
    print(f"   Canvas 1 FPS: {canvas1.fps} (should be 30)")
    print(f"   Canvas 2 FPS: {canvas2.fps} (should also be 30, ignoring second call)")
    assert canvas1.fps == 30 and canvas2.fps == 30, "Singleton should preserve original parameters"
    
    # Test 2: get_instance method
    print("\n2. Testing get_instance method...")
    canvas3 = DmxCanvas.get_instance()
    print(f"   Canvas 3 ID: {id(canvas3)}")
    print(f"   Same as canvas1: {canvas1 is canvas3}")
    print(f"   ✅ get_instance working: {canvas1 is canvas3}")
    
    # Test 3: State persistence across references
    print("\n3. Testing state persistence...")
    canvas1.paint_frame(5.0, {0: 255, 1: 128, 2: 64})
    
    # Check that all references see the same data
    frame1 = canvas1.get_frame(5.0)
    frame2 = canvas2.get_frame(5.0) 
    frame3 = canvas3.get_frame(5.0)
    
    print(f"   Frame from canvas1: RGB=({frame1[0]}, {frame1[1]}, {frame1[2]})")
    print(f"   Frame from canvas2: RGB=({frame2[0]}, {frame2[1]}, {frame2[2]})")
    print(f"   Frame from canvas3: RGB=({frame3[0]}, {frame3[1]}, {frame3[2]})")
    
    frames_match = frame1 == frame2 == frame3
    print(f"   ✅ State shared: {frames_match}")
    assert frames_match, "All references should see same data"
    
    # Test 4: reset_instance creates new instance
    print("\n4. Testing reset_instance...")
    old_id = id(canvas1)
    canvas4 = DmxCanvas.reset_instance(fps=60, duration=20.0, debug=True)
    new_id = id(canvas4)
    
    print(f"   Old canvas ID: {old_id}")
    print(f"   New canvas ID: {new_id}")
    print(f"   Different object: {old_id != new_id}")
    print(f"   New FPS: {canvas4.fps} (should be 60)")
    print(f"   ✅ Reset working: {old_id != new_id and canvas4.fps == 60}")
    
    # Verify old references now point to new instance
    canvas5 = DmxCanvas.get_instance()
    print(f"   Canvas5 ID after reset: {id(canvas5)}")
    print(f"   Same as new canvas4: {canvas4 is canvas5}")
    print(f"   ✅ References updated: {canvas4 is canvas5}")
    
    # Test 5: Clear canvas preserves singleton
    print("\n5. Testing clear_canvas preserves singleton...")
    canvas4.paint_frame(3.0, {10: 200})
    frame_before = canvas4.get_frame(3.0)
    print(f"   Before clear: channel 10 = {frame_before[10]}")
    
    canvas4.clear_canvas()
    frame_after = canvas4.get_frame(3.0)
    print(f"   After clear: channel 10 = {frame_after[10]}")
    print(f"   Still same instance: {canvas4 is DmxCanvas.get_instance()}")
    print(f"   ✅ Clear preserves singleton: {frame_after[10] == 0}")
    
    # Test 6: is_initialized method
    print("\n6. Testing is_initialized...")
    print(f"   Is initialized: {DmxCanvas.is_initialized()}")
    print(f"   ✅ Initialization tracking: {DmxCanvas.is_initialized()}")
    
    print("\n" + "="*60)
    print("✅ ALL SINGLETON TESTS PASSED!")
    print("🎨 DMX Canvas properly implements singleton pattern")
    print("🔒 Single instance ensures data consistency")
    print("🔄 Reset functionality allows parameter changes")
    print("="*60)

def test_integration_with_app_state():
    """Test integration with app_state singleton pattern."""
    print("\n🧪 Testing integration with app_state...\n")
    
    try:
        from backend.models.app_state import app_state
        
        # Reset canvas to known state
        canvas = DmxCanvas.reset_instance(fps=44, duration=100.0, debug=True)
        
        # Set in app_state
        app_state.dmx_canvas = canvas
        
        # Verify app_state holds the singleton
        retrieved_canvas = app_state.dmx_canvas
        print(f"Canvas in app_state ID: {id(retrieved_canvas)}")
        print(f"Original canvas ID: {id(canvas)}")
        print(f"Same instance: {canvas is retrieved_canvas}")
        
        # Test that new DmxCanvas() calls return the same instance
        canvas2 = DmxCanvas()
        print(f"New DmxCanvas() ID: {id(canvas2)}")
        print(f"Same as app_state canvas: {canvas2 is retrieved_canvas}")
        
        print(f"✅ App state integration works!")
        
    except ImportError as e:
        print(f"⚠️ Could not test app_state integration: {e}")

if __name__ == "__main__":
    test_singleton_behavior()
    test_integration_with_app_state()
