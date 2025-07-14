#!/usr/bin/env python
"""
Tests for the DMX Canvas module.

This module contains tests for the DmxCanvas class to verify its functionality.
"""
import unittest
import numpy as np
from backend.services.dmx.dmx_canvas import DmxCanvas


class TestDmxCanvas(unittest.TestCase):
    """Test cases for the DmxCanvas class."""

    def test_init(self):
        """Test canvas initialization."""
        canvas = DmxCanvas(fps=30, duration=10.0)
        self.assertEqual(canvas.fps, 30)
        self.assertEqual(canvas.duration, 10.0)
        self.assertEqual(canvas.frame_duration, 1/30)
        self.assertEqual(canvas.num_frames, 300)  # 10s * 30fps
        self.assertEqual(canvas.universe_size, 512)

    def test_paint_frame(self):
        """Test painting a single frame."""
        canvas = DmxCanvas(fps=30, duration=10.0)
        canvas.paint_frame(1.0, {10: 255, 11: 128, 12: 64})
        
        frame = canvas.get_frame(1.0)
        self.assertEqual(frame[10], 255)
        self.assertEqual(frame[11], 128)
        self.assertEqual(frame[12], 64)
        self.assertEqual(frame[13], 0)  # Unpainted channel should be 0

    def test_paint_range(self):
        """Test painting a range of frames."""
        canvas = DmxCanvas(fps=30, duration=10.0)
        
        def fade_in(t):
            progress = (t - 2.0) / 3.0  # From t=2 to t=5
            value = int(255 * progress)
            return {20: value, 21: value}
        
        canvas.paint_range(2.0, 5.0, fade_in)
        
        # Check frame at start of range
        frame_start = canvas.get_frame(2.0)
        self.assertEqual(frame_start[20], 0)
        
        # Check frame in middle of range
        frame_mid = canvas.get_frame(3.5)
        expected_value = int(255 * (3.5 - 2.0) / 3.0)
        self.assertEqual(frame_mid[20], expected_value)
        self.assertEqual(frame_mid[21], expected_value)
        
        # Check frame at end of range
        frame_end = canvas.get_frame(5.0)
        self.assertEqual(frame_end[20], 255)
        self.assertEqual(frame_end[21], 255)

    def test_get_frame(self):
        """Test getting frames at different timestamps."""
        canvas = DmxCanvas(fps=30, duration=10.0)
        canvas.paint_frame(1.0, {10: 255})
        
        # Test exact timestamp
        self.assertEqual(canvas.get_frame(1.0)[10], 255)
        
        # Test timestamps close to 1.0 (should get the same frame)
        self.assertEqual(canvas.get_frame(1.01)[10], 255)
        self.assertEqual(canvas.get_frame(0.99)[10], 255)
        
        # Test timestamp out of range (clamps to valid range)
        self.assertEqual(len(canvas.get_frame(-1.0)), 512)
        self.assertEqual(len(canvas.get_frame(20.0)), 512)

    def test_export(self):
        """Test exporting the entire canvas."""
        canvas = DmxCanvas(fps=10, duration=1.0)  # 10 frames total
        
        # Paint some frames
        canvas.paint_frame(0.1, {1: 10})
        canvas.paint_frame(0.5, {2: 20})
        
        # Export and check
        timeline = canvas.export()
        self.assertEqual(len(timeline), 10)  # Should have 10 frames
        self.assertEqual(timeline[0.1][1], 10)
        self.assertEqual(timeline[0.5][2], 20)
        
        # Check that all frames are 512 bytes
        for timestamp, frame in timeline.items():
            self.assertEqual(len(frame), 512)


if __name__ == "__main__":
    unittest.main()
