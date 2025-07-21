#!/usr/bin/env python3
"""
Test script to verify that the canvas duration fix works correctly.
This test creates a canvas with song duration + 2 seconds and exports it to verify the timeline.
"""

from backend.config import SONGS_DIR
from shared.models.song_metadata import SongMetadata
from backend.services.dmx.dmx_canvas import DmxCanvas
from shared.file_utils import save_file

print("🎵 Testing Canvas Duration Fix...")

# 1. Load born_slippy song metadata
print("1. Loading born_slippy song metadata...")
song_metadata = SongMetadata(
    song_name="born_slippy",
    songs_folder=str(SONGS_DIR),
)
print(f"   📊 Song duration: {song_metadata.duration:.2f}s")

# 2. Initialize canvas with song duration + 2 seconds for final effects
canvas_duration = song_metadata.duration + 2.0
print(f"2. Initializing canvas with duration: {canvas_duration:.2f}s (song: {song_metadata.duration:.2f}s + 2s)")
dmx_canvas = DmxCanvas.reset_instance(
    fps=44,
    duration=canvas_duration,
    debug=True
)

# 3. Paint some test data across the timeline
print("3. Painting test data across the timeline...")
# Paint a flash at the beginning
dmx_canvas.paint_frame(0.0, {16: 255, 17: 255, 18: 255})

# Paint a flash in the middle of the song
middle_time = song_metadata.duration / 2
dmx_canvas.paint_frame(middle_time, {19: 255, 20: 255, 21: 255})

# Paint a flash at the end of the song
dmx_canvas.paint_frame(song_metadata.duration - 1.0, {22: 255, 23: 255, 24: 255})

# Paint a final effect in the extra 2 seconds
final_effect_time = song_metadata.duration + 1.0
dmx_canvas.paint_frame(final_effect_time, {25: 255, 26: 255, 27: 255})

print(f"   ✅ Painted test data at: 0.0s, {middle_time:.1f}s, {song_metadata.duration - 1.0:.1f}s, {final_effect_time:.1f}s")

# 4. Export the full canvas timeline
print("4. Exporting full canvas timeline...")
canvas_export = dmx_canvas.export_as_txt(
    start_time=0, 
    end_time=canvas_duration,
    start_channel=16,
    end_channel=27
)

# 5. Save to file
print("5. Saving canvas export to file...")
import os
os.makedirs(song_metadata.data_folder, exist_ok=True)
output_file = f"{song_metadata.data_folder}/{song_metadata.song_name}.canvas.txt"
save_file(output_file, canvas_export)
print(f"   💾 Saved to: {output_file}")

# 6. Analyze the export
print("6. Analyzing the export...")
lines = canvas_export.split('\n')
data_lines = [line for line in lines if line and line[0].isdigit()]  # Only lines starting with a digit (timestamps)

if data_lines:
    first_line = data_lines[0]
    last_line = data_lines[-1]
    
    # Extract timestamps from first and last lines
    first_time = float(first_line.split(' | ')[0])
    last_time = float(last_line.split(' | ')[0])
    
    print(f"   📈 Canvas timeline: {first_time:.3f}s to {last_time:.3f}s")
    print(f"   📏 Actual duration: {last_time:.3f}s")
    print(f"   🎯 Expected duration: {canvas_duration:.3f}s")
    print(f"   ✅ Duration match: {'YES' if abs(last_time - canvas_duration) < 1.0 else 'NO'}")
    
    # Show some key timestamps
    print(f"   🔍 Data frames: {len(data_lines)} total")
    print(f"   📊 First few lines:")
    for i, line in enumerate(data_lines[:3]):  # First 3 lines
        print(f"      {line}")
    print(f"   📊 Last few lines:")
    for i, line in enumerate(data_lines[-3:]):  # Last 3 lines
        print(f"      {line}")

print("✅ Canvas duration fix test complete!")
