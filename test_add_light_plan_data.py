#!/usr/bin/env python3
"""Test script to add light plan data to a song metadata file."""

import sys
import os
sys.path.append('/home/darkangel/ai-light-show')

from shared.models.song_metadata import SongMetadata, LightPlanItem

def test_add_light_plan_to_song():
    """Add some test light plan data to born_slippy.mp3."""
    
    songs_folder = "/home/darkangel/ai-light-show/songs"
    
    # Load the song metadata
    song = SongMetadata("born_slippy.mp3", songs_folder=songs_folder)
    
    print(f"📀 Loaded song: {song.title}")
    print(f"🎵 Duration: {song.duration:.2f} seconds")
    print(f"💡 Current light plan items: {len(song.light_plan)}")
    
    # Clear existing light plan and add test items
    song.clear_light_plan()
    
    # Add some example light plan items
    song.add_light_plan_item(1, 0.0, 30.0, "Intro Warmup", "Soft warm lighting for intro")
    song.add_light_plan_item(2, 30.0, 60.0, "Build Up", "Gradually increase intensity")
    song.add_light_plan_item(3, 60.0, 90.0, "First Drop", "High energy strobing and movement")
    song.add_light_plan_item(4, 90.0, 120.0, "Bridge", "Ambient purple lighting")
    song.add_light_plan_item(5, 120.0, 150.0, "Second Drop", "Maximum intensity with all fixtures")
    song.add_light_plan_item(6, 150.0, None, "Outro", "Gradual fade out to black")
    
    # Save the updated metadata
    song.save()
    
    print(f"✅ Added {len(song.light_plan)} light plan items:")
    for item in song.light_plan:
        end_str = f" to {item.end:.2f}s" if item.end else " (no end)"
        print(f"   - {item.name}: {item.start:.2f}s{end_str} - {item.description}")
    
    print("\n🎉 Light plan data added successfully!")
    print("   You can now test the LightingPlan component in the web interface.")

if __name__ == "__main__":
    test_add_light_plan_to_song()
