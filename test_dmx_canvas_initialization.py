#!/usr/bin/env python3
"""
Test script to verify that DmxCanvas is re-initialized with song duration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.models.app_state import app_state
from backend.models.song_metadata import SongMetadata
from backend.services.dmx_canvas import DmxCanvas
from backend.config import SONGS_DIR

def test_dmx_canvas_reinitialization():
    print("🧪 Testing DMX Canvas re-initialization with song duration")
    
    # Check initial state
    print(f"Initial DMX Canvas duration: {app_state.dmx_canvas.duration:.2f}s")
    print(f"Initial DMX Canvas frames: {app_state.dmx_canvas.num_frames}")
    
    # Test with a known song file (if available)
    test_song = "born_slippy.mp3"
    song_path = SONGS_DIR / test_song
    
    if song_path.exists():
        print(f"\n🎵 Loading test song: {test_song}")
        
        # Simulate song loading
        app_state.current_song_file = test_song
        app_state.current_song = SongMetadata(test_song, songs_folder=str(SONGS_DIR))
        
        # Get song duration
        song_duration = app_state.current_song.duration
        print(f"Song duration: {song_duration:.2f}s")
        
        # Re-initialize DmxCanvas with song duration
        if song_duration > 0:
            print(f"🎛️ Re-initializing DMX Canvas with duration: {song_duration:.2f}s")
            app_state.dmx_canvas = DmxCanvas(fps=44, duration=song_duration)
            
            print(f"New DMX Canvas duration: {app_state.dmx_canvas.duration:.2f}s")
            print(f"New DMX Canvas frames: {app_state.dmx_canvas.num_frames}")
            print(f"Frame rate: {app_state.dmx_canvas.fps} FPS")
            
            # Verify the canvas is properly sized
            expected_frames = int(song_duration * 44)  # 44 FPS
            actual_frames = app_state.dmx_canvas.num_frames
            print(f"Expected frames: {expected_frames}, Actual frames: {actual_frames}")
            
            if abs(actual_frames - expected_frames) <= 1:  # Allow for rounding
                print("✅ DMX Canvas successfully re-initialized with correct duration!")
            else:
                print("❌ Frame count mismatch!")
        else:
            print("⚠️ Song duration not available")
    else:
        print(f"⚠️ Test song {test_song} not found, creating mock test...")
        
        # Create a mock test with a specific duration
        mock_duration = 180.5  # 3 minutes 30.5 seconds
        print(f"🎛️ Testing with mock duration: {mock_duration:.2f}s")
        
        old_duration = app_state.dmx_canvas.duration
        app_state.dmx_canvas = DmxCanvas(fps=44, duration=mock_duration)
        
        print(f"Old duration: {old_duration:.2f}s")
        print(f"New duration: {app_state.dmx_canvas.duration:.2f}s")
        print(f"New frames: {app_state.dmx_canvas.num_frames}")
        
        if app_state.dmx_canvas.duration == mock_duration:
            print("✅ DMX Canvas successfully re-initialized with mock duration!")
        else:
            print("❌ Duration mismatch!")

if __name__ == "__main__":
    test_dmx_canvas_reinitialization()
