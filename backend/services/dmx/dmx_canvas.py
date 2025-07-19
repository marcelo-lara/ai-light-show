#!/usr/bin/env python
"""
DMX Canvas module for AI Light Show.

This module provides a canvas for storing and manipulating DMX state over time.
It represents a sequence of 512-byte DMX frames that can be painted with channel values
at specific timestamps.
"""
import numpy as np
from typing import Dict, Callable, Optional
import math


class DmxCanvas:
    """
    Singleton DMX Canvas for storing and manipulating DMX state over time.
    
    This ensures only one DMX canvas instance exists throughout the application,
    maintaining consistency across all services and preventing conflicts.
    """
    _instance = None
    """
    A canvas for storing and manipulating DMX state over time.
    
    The DmxCanvas represents a sequence of DMX universe states (512 channels),
    quantized at a specific frame rate. It allows painting values at specific timestamps
    and retrieving the complete DMX frame at any point in time.
    
    Attributes:
        fps (int): Frames per second for the timeline.
        duration (float): Total duration of the timeline in seconds.
        frame_duration (float): Duration of a single frame in seconds.
        num_frames (int): Total number of frames in the timeline.
        universe_size (int): Size of the DMX universe (512 channels).
        _timeline (Dict[float, bytes]): Internal storage mapping timestamps to DMX frames.
        _canvas (np.ndarray): NumPy array for efficient frame manipulation.
    """
    
    def __new__(cls, fps: int = 44, duration: float = 300.0, debug: Optional[bool] = False):
        """
        Singleton implementation - ensures only one DMX canvas exists.
        
        Args:
            fps (int): Frames per second for the timeline. Defaults to 44.
            duration (float): Total duration of the timeline in seconds. Defaults to 300.0.
            debug (bool): Enable debug logging. Defaults to False.
            
        Returns:
            DmxCanvas: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = super(DmxCanvas, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, fps: int = 44, duration: float = 300.0, debug: Optional[bool] = False):
        """
        Initialize the DMX canvas (only runs once for singleton).
        
        Args:
            fps (int): Frames per second for the timeline. Defaults to 44.
            duration (float): Total duration of the timeline in seconds. Defaults to 300.0.
            debug (bool): Enable debug logging. Defaults to False.
        """
        # Only initialize once - subsequent calls will reuse existing instance
        if hasattr(self, '_initialized') and self._initialized:
            if debug:
                print(f"⚠️ DMX Canvas already initialized. Using existing instance.")
                print(f"   Current: {self._num_frames} frames ({self.duration}s at {self.fps} FPS)")
            return
            
        self.fps = fps
        self.duration = duration
        self.frame_duration = 1.0 / fps
        self._num_frames = math.ceil(duration * fps)
        self.universe_size = 512
        self.debug = debug
        
        # Initialize the canvas with zeros
        # Each frame is a 512-byte array representing the DMX universe state
        # The canvas is initialized to zero (all channels off)
        
        if self.debug:
            print(f"🎨 Initializing DMX Canvas Singleton: {self._num_frames} frames, {self.universe_size} channels")
        
        # Internal storage as NumPy array for performance
        self._canvas = np.zeros((self._num_frames, self.universe_size), dtype=np.uint8)
        
        # Timeline dictionary for final storage and export
        self._timeline = {}
        
        # Mark as initialized
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'DmxCanvas':
        """
        Get the singleton instance of the DMX canvas.
        
        Returns:
            DmxCanvas: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls, fps: int = 44, duration: float = 300.0, debug: Optional[bool] = False) -> 'DmxCanvas':
        """
        Reset the singleton instance with new parameters.
        
        This destroys the existing instance and creates a new one with the specified parameters.
        Use this when you need to change the canvas dimensions or settings.
        
        Args:
            fps (int): Frames per second for the timeline. Defaults to 44.
            duration (float): Total duration of the timeline in seconds. Defaults to 300.0.
            debug (bool): Enable debug logging. Defaults to False.
            
        Returns:
            DmxCanvas: The new singleton instance.
        """
        if cls._instance is not None and debug:
            print(f"🔄 Resetting DMX Canvas Singleton")
            print(f"   Old: {cls._instance._num_frames} frames ({cls._instance.duration}s at {cls._instance.fps} FPS)")
            print(f"   New: {math.ceil(duration * fps)} frames ({duration}s at {fps} FPS)")
        
        cls._instance = None
        return cls(fps=fps, duration=duration, debug=debug)
    
    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if the singleton instance has been initialized.
        
        Returns:
            bool: True if initialized, False otherwise.
        """
        return cls._instance is not None and hasattr(cls._instance, '_initialized') and cls._instance._initialized
    
    @property
    def num_frames(self) -> int:
        """
        Get the total number of frames in the timeline.
        
        Returns:
            int: Total number of frames.
        """
        return self._num_frames
    
    def _time_to_frame_index(self, timestamp: float) -> int:
        """
        Convert a timestamp to the nearest frame index.
        
        Args:
            timestamp (float): Time in seconds.
            
        Returns:
            int: The nearest frame index.
        """
        frame_index = round(timestamp * self.fps)
        return max(0, min(frame_index, self._num_frames - 1))
    
    def _frame_index_to_time(self, frame_index: int) -> float:
        """
        Convert a frame index to its timestamp.
        
        Args:
            frame_index (int): Index of the frame.
            
        Returns:
            float: Time in seconds, rounded to 4 decimal places.
        """
        return round(frame_index * self.frame_duration, 4)
    
    def paint_frame(self, timestamp: float, channel_values: Dict[int, int]) -> None:
        """
        Paint DMX channel values at a specific timestamp.
        
        Args:
            timestamp (float): Time in seconds where the values should be applied.
            channel_values (Dict[int, int]): Dictionary mapping channel numbers to values (0-255).
        """
        frame_index = self._time_to_frame_index(timestamp)
        
        # Apply the channel values to the frame
        for channel, value in channel_values.items():
            if 0 <= channel < self.universe_size:
                self._canvas[frame_index, channel] = min(255, max(0, value))
    
    def paint_channel(self, channel: int, start_time: float, duration: float,
                     value_fn: Callable[[float], int]) -> None:
        """
        Paint a single channel's values over a time range.
        
        Args:
            channel (int): DMX channel number (0-511)
            start_time (float): Start time in seconds
            duration (float): Duration in seconds
            value_fn (Callable[[float], int]): Function that takes time offset (0-1)
                and returns channel value (0-255)
        """
        if not 0 <= channel < self.universe_size:
            return
            
        start_frame = self._time_to_frame_index(start_time)
        end_frame = self._time_to_frame_index(start_time + duration)
        
        for frame_index in range(start_frame, end_frame + 1):
            frame_time = self._frame_index_to_time(frame_index)
            time_offset = (frame_time - start_time) / duration
            if 0 <= time_offset <= 1:
                self._canvas[frame_index, channel] = min(255, max(0, 
                    value_fn(time_offset)))

    def paint_range(self, start: float, end: float, 
                   channel_values_fn: Callable[[float], Dict[int, int]]) -> None:
        """
        Apply a function to paint channel values across a time range.
        
        Args:
            start (float): Start time in seconds.
            end (float): End time in seconds.
            channel_values_fn (Callable[[float], Dict[int, int]]): Function that takes a timestamp 
                and returns a dictionary of channel values.
        """
        start_frame = self._time_to_frame_index(start)
        end_frame = self._time_to_frame_index(end)
        
        for frame_index in range(start_frame, end_frame + 1):
            timestamp = self._frame_index_to_time(frame_index)
            channel_values = channel_values_fn(timestamp)
            
            # Apply the channel values to the frame
            for channel, value in channel_values.items():
                if 0 <= channel < self.universe_size:
                    self._canvas[frame_index, channel] = min(255, max(0, value))
    
    def get_frame(self, timestamp: float) -> bytes:
        """
        Get the DMX frame at the specified timestamp.
        
        Args:
            timestamp (float): Time in seconds.
            
        Returns:
            bytes: A 512-byte array representing the DMX universe state.
        """
        frame_index = self._time_to_frame_index(timestamp)
        return bytes(self._canvas[frame_index])
    
    def export(self) -> Dict[float, bytes]:
        """
        Export the complete DMX canvas.
        
        Returns:
            Dict[float, bytes]: Dictionary mapping timestamps to DMX frames.
        """
        # Convert the NumPy array to a timeline dictionary
        timeline = {}
        for frame_index in range(self._num_frames):
            timestamp = self._frame_index_to_time(frame_index)
            timeline[timestamp] = bytes(self._canvas[frame_index])
        
        return timeline

    def clear_canvas(self) -> None:
        """
        Clear the entire DMX canvas, resetting all channels to zero.
        This preserves the singleton instance while clearing all data.
        """
        # Reset the entire canvas to zeros
        self._canvas.fill(0)
        
        # Clear the timeline dictionary as well
        self._timeline.clear()
        
        if self.debug:
            print(f"🧹 DMX Canvas Singleton cleared: {self._num_frames} frames, {self.universe_size} channels reset to 0")

    def export_as_txt(self, start_time: float = 0, end_time: float = 0.5, start_channel: int = 16, end_channel: int = 39) -> str:
        """
        Export the DMX canvas as a log string.
        This method formats the timeline into a human-readable string,
        with each line containing the timestamp and the corresponding DMX frame in int format.
        
        Args:
            start_time (float): Start time for the export (default: 0).
            end_time (float): End time for the export (default: entire canvas).
            start_channel (int): Start channel for the export (1-based index) (default: 1).
            end_channel (int): End channel for the export (1-based index) (default: 512).

        Returns:
            str: Formatted log string.
        """
        # Clamp channel indices to valid range
        start_channel = max(1, min(start_channel, self.universe_size))
        end_channel = max(1, min(end_channel, self.universe_size))
        if end_channel < start_channel:
            end_channel = start_channel

        # Calculate frame indices for time range
        start_frame = self._time_to_frame_index(start_time)
        if end_time == 0:
            end_frame = self._num_frames - 1
        else:
            end_frame = self._time_to_frame_index(end_time)
    
        if end_frame < start_frame:
            end_frame = start_frame

        # Header for selected channels
        log_lines = []
        log_lines.append(
            "time  | " + ".".join(f"{i:03}" for i in range(start_channel, end_channel + 1))
        )
        log_lines.append("----- | " + "-" * (4 * (end_channel - start_channel + 1)))

        # Iterate through the selected frames and format each
        for frame_index in range(start_frame, end_frame + 1):
            timestamp = self._frame_index_to_time(frame_index)
            frame = self._canvas[frame_index]
            selected_values = frame[start_channel - 1:end_channel]
            # Format each value, replacing '000' with blanks for better readability
            frame_values = [f"{value:03}" if value != 0 else "   " for value in selected_values]
            line = f"{timestamp:.3f} | {'.'.join(frame_values)}"
            log_lines.append(line)
        return "\n".join(log_lines)



if __name__ == "__main__":
    # Example usage demonstrating singleton behavior
    print("🧪 Testing DMX Canvas Singleton")
    
    # Create first instance
    canvas1 = DmxCanvas(fps=30, duration=10.0, debug=True)
    print(f"Canvas 1 ID: {id(canvas1)}")
    
    # Create second instance - should be the same object
    canvas2 = DmxCanvas(fps=60, duration=20.0, debug=True)  # Parameters ignored
    print(f"Canvas 2 ID: {id(canvas2)}")
    print(f"Same instance: {canvas1 is canvas2}")
    
    # Use get_instance method
    canvas3 = DmxCanvas.get_instance()
    print(f"Canvas 3 ID: {id(canvas3)}")
    print(f"Same instance: {canvas1 is canvas3}")
    
    # Reset to create new instance with different parameters
    canvas4 = DmxCanvas.reset_instance(fps=60, duration=20.0, debug=True)
    print(f"Canvas 4 ID: {id(canvas4)}")
    print(f"Different instance after reset: {canvas1 is not canvas4}")
    
    # Paint a single frame
    canvas4.paint_frame(1.0, {10: 255, 11: 128, 12: 64})
    
    # Paint a range with a function
    def fade_in(t: float) -> Dict[int, int]:
        # Calculate value based on time (linear fade from 0 to 255)
        progress = (t - 2.0) / 3.0  # From t=2 to t=5, progress goes from 0 to 1
        value = int(255 * progress)
        return {20: value, 21: value, 22: value}
    
    canvas4.paint_range(2.0, 5.0, fade_in)
    
    # Export as text
    log_output = canvas4.export_as_txt(start_channel=10, end_channel=22)
    print("\nExported log:")
    print(log_output[:500])  # Print first 500 characters of the log