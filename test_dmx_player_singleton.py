#!/usr/bin/env python3
"""
Test script to verify DMX Player uses DmxCanvas singleton and proper blackout behavior.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from backend.services.dmx.dmx_player import DmxPlayer
from backend.services.dmx.dmx_canvas import DmxCanvas

async def test_dmx_player_singleton_usage():
    """Test that DMX player uses DmxCanvas singleton correctly."""
    print("🧪 Testing DMX Player with DmxCanvas Singleton\n")
    
    # Reset canvas to ensure clean test
    canvas = DmxCanvas.reset_instance(fps=44, duration=10.0, debug=True)
    
    # Paint some test data
    canvas.paint_frame(timestamp=2.0, channel_values={0: 255, 1: 128, 2: 64})
    canvas.paint_frame(timestamp=5.0, channel_values={10: 200, 11: 150, 12: 100})
    
    player = DmxPlayer(fps=10)  # Low FPS for testing
    
    print("1. Testing singleton canvas access...")
    
    # Test direct frame retrieval
    frame_2s = player._retrieve_dmx_frame(2.0)
    frame_5s = player._retrieve_dmx_frame(5.0)
    
    print(f"   Frame at 2.0s: RGB=({frame_2s[0]}, {frame_2s[1]}, {frame_2s[2]})")
    print(f"   Frame at 5.0s: channels 10-12=({frame_5s[10]}, {frame_5s[11]}, {frame_5s[12]})")
    
    # Verify data matches what we painted
    assert frame_2s[0] == 255 and frame_2s[1] == 128 and frame_2s[2] == 64, "Frame at 2s mismatch"
    assert frame_5s[10] == 200 and frame_5s[11] == 150 and frame_5s[12] == 100, "Frame at 5s mismatch"
    
    print("   ✅ Singleton canvas access working correctly")
    
    # Test when canvas is not initialized
    print("\n2. Testing behavior with uninitialized canvas...")
    
    # Temporarily clear the singleton
    DmxCanvas._instance = None
    
    frame_empty = player._retrieve_dmx_frame(2.0)
    print(f"   Frame with no canvas: sum={sum(frame_empty)} (should be 0)")
    assert sum(frame_empty) == 0, "Should return blackout when no canvas"
    
    print("   ✅ Proper fallback when canvas not available")
    
    # Restore canvas
    canvas = DmxCanvas.reset_instance(fps=44, duration=10.0)
    canvas.paint_frame(timestamp=2.0, channel_values={0: 255, 1: 128, 2: 64})
    
    print("\n3. Testing singleton persistence...")
    
    # Create another player - should use same canvas
    player2 = DmxPlayer()
    frame_2s_player2 = player2._retrieve_dmx_frame(2.0)
    
    print(f"   Player1 frame: RGB=({frame_2s[0]}, {frame_2s[1]}, {frame_2s[2]})")
    print(f"   Player2 frame: RGB=({frame_2s_player2[0]}, {frame_2s_player2[1]}, {frame_2s_player2[2]})")
    
    assert frame_2s_player2[0] == 255, "Both players should see same singleton data"
    print("   ✅ Multiple players use same singleton canvas")

async def test_blackout_behavior():
    """Test conditional blackout transmission behavior."""
    print("\n🧪 Testing Blackout Transmission Behavior\n")
    
    sent_packets = []
    sent_times = []
    
    def mock_send_artnet(universe, current_time=None, debug=False):
        sent_packets.append(list(universe))
        sent_times.append(current_time)
    
    with patch('backend.services.dmx.dmx_player.send_artnet', side_effect=mock_send_artnet):
        # Setup canvas with data
        canvas = DmxCanvas.reset_instance(fps=44, duration=10.0)
        canvas.paint_frame(timestamp=2.0, channel_values={0: 255})
        
        # Test 1: blackout_when_not_playing = False (default)
        print("1. Testing blackout_when_not_playing = False...")
        
        player = DmxPlayer(fps=10)
        player.blackout_when_not_playing = False
        
        sent_packets.clear()
        sent_times.clear()
        
        await player.start_playback_engine()
        
        # Not playing - should send NO frames
        await asyncio.sleep(0.15)
        not_playing_packets = len(sent_packets)
        
        print(f"   Packets sent while not playing: {not_playing_packets}")
        
        # Start playing - should send frames
        player.sync_playback(True, 2.0)
        await asyncio.sleep(0.15)
        
        playing_packets = len(sent_packets) - not_playing_packets
        lit_packets = len([p for p in sent_packets[not_playing_packets:] if p[0] > 0])
        
        print(f"   Packets sent while playing: {playing_packets}")
        print(f"   Packets with channel 0 > 0: {lit_packets}")
        
        # Stop playing - should send NO frames again
        packets_before_pause = len(sent_packets)
        player.sync_playback(False, 2.0)
        await asyncio.sleep(0.15)
        
        paused_packets = len(sent_packets) - packets_before_pause
        print(f"   Packets sent while paused: {paused_packets}")
        
        await player.stop_playback_engine()
        
        assert not_playing_packets == 0, "Should send NO packets when not playing and blackout=False"
        assert playing_packets > 0, "Should send packets when playing"
        assert paused_packets == 0, "Should send NO packets when paused and blackout=False"
        
        print("   ✅ Conditional transmission working (no frames when blackout=False)")
        
        # Test 2: blackout_when_not_playing = True
        print("\n2. Testing blackout_when_not_playing = True...")
        
        player2 = DmxPlayer(fps=10)
        player2.blackout_when_not_playing = True
        
        sent_packets.clear()
        sent_times.clear()
        
        await player2.start_playback_engine()
        
        # Not playing - should send blackout frames
        await asyncio.sleep(0.15)
        not_playing_packets = len(sent_packets)
        blackout_packets = len([p for p in sent_packets if sum(p) == 0])
        
        print(f"   Packets sent while not playing: {not_playing_packets}")
        print(f"   Blackout packets (sum=0): {blackout_packets}")
        
        # Start playing - should send lit frames
        player2.sync_playback(True, 2.0)
        await asyncio.sleep(0.15)
        
        playing_packets = len(sent_packets) - not_playing_packets
        lit_packets = len([p for p in sent_packets[not_playing_packets:] if p[0] > 0])
        
        print(f"   Packets sent while playing: {playing_packets}")
        print(f"   Packets with channel 0 > 0: {lit_packets}")
        
        # Stop playing - should send blackout frames again
        packets_before_pause = len(sent_packets)
        player2.sync_playback(False, 2.0)
        await asyncio.sleep(0.15)
        
        paused_packets = len(sent_packets) - packets_before_pause
        paused_blackout = len([p for p in sent_packets[packets_before_pause:] if sum(p) == 0])
        
        print(f"   Packets sent while paused: {paused_packets}")
        print(f"   Blackout packets while paused: {paused_blackout}")
        
        await player2.stop_playback_engine()
        
        assert not_playing_packets > 0 and blackout_packets == not_playing_packets, "Should send blackout when not playing and blackout=True"
        assert playing_packets > 0 and lit_packets > 0, "Should send lit frames when playing"
        assert paused_packets > 0 and paused_blackout == paused_packets, "Should send blackout when paused and blackout=True"
        
        print("   ✅ Conditional transmission working (blackout frames when blackout=True)")

async def main():
    """Run all tests."""
    print("🚀 Testing DMX Player Singleton and Blackout Behavior\n")
    
    try:
        await test_dmx_player_singleton_usage()
        await test_blackout_behavior()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("🎨 DMX Player correctly uses DmxCanvas singleton")
        print("📡 Blackout transmission properly controlled by flag")
        print("🔒 No frames sent when blackout_when_not_playing=False")
        print("⚫ Blackout frames sent when blackout_when_not_playing=True")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
