"""
DMX Player Service - Handles playback timing and DMX universe dispatching.

This service manages the real-time playback of lighting shows, synchronizing
audio timing with DMX canvas dispatching.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from .dmx_dispatcher import send_artnet


@dataclass
class PlaybackState:
    """Manages playback timing and state."""
    is_playing: bool = False
    playback_time: float = 0.0
    start_monotonic: float = 0.0
    last_sent: float = 0.0
    
    def get_current_time(self) -> float:
        """Get the current playback time based on monotonic clock."""
        if not self.is_playing:
            return self.playback_time
        
        elapsed = time.monotonic() - self.start_monotonic
        return self.playback_time + elapsed
    
    def seek_to(self, time_position: float) -> None:
        """Seek to a specific time position."""
        self.playback_time = time_position
        if self.is_playing:
            self.start_monotonic = time.monotonic()
    
    def play(self) -> None:
        """Start playback."""
        if not self.is_playing:
            self.is_playing = True
            self.start_monotonic = time.monotonic()
    
    def pause(self) -> None:
        """Pause playback."""
        if self.is_playing:
            self.playback_time = self.get_current_time()
            self.is_playing = False
    
    def stop(self) -> None:
        """Stop playback and reset to beginning."""
        self.is_playing = False
        self.playback_time = 0.0
        self.start_monotonic = 0.0


class DmxPlayer:
    """
    DMX Player manages real-time playback and DMX output.
    
    This service handles:
    - Playback timing synchronization
    - DMX universe dispatch from singleton DmxCanvas
    - Real-time Art-Net output
    - Conditional blackout transmission
    """
    
    def __init__(self, fps: int = 60):
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.playback_state = PlaybackState()
        self.is_running = False
        self._render_task: Optional[asyncio.Task] = None
        self._on_frame_callback: Optional[Callable[[float, bytes], None]] = None
        self.blackout_when_not_playing: bool = False  # Whether to send blackout frames when not playing

    def set_frame_callback(self, callback: Callable[[float, bytes], None]) -> None:
        """Set a callback to be called for each rendered frame."""
        self._on_frame_callback = callback
    
    async def start_playback_engine(self) -> None:
        """Start the DMX playback engine."""
        if self.is_running:
            return
            
        self.is_running = True
        self._render_task = asyncio.create_task(self._dispatcher_loop())
        print(f"🎬 DMX Player started at {self.fps} FPS")
    
    async def stop_playback_engine(self) -> None:
        """Stop the DMX playback engine."""
        self.is_running = False
        if self._render_task:
            self._render_task.cancel()
            try:
                await self._render_task
            except asyncio.CancelledError:
                pass
            self._render_task = None
        print("🛑 DMX Player stopped")
    
    async def _dispatcher_loop(self) -> None:
        """Main rendering loop - runs at specified FPS."""
        
        try:
            while self.is_running:
                # Get current playback time
                current_time = self.playback_state.get_current_time()
                
                # Render frame based on song time and playback state
                if self.playback_state.is_playing:
                    # Render DMX universe from singleton canvas at current song time
                    dmx_universe = self._retrieve_dmx_frame(current_time)
                    
                    # Send Art-Net packet with rendered lighting data
                    send_artnet(dmx_universe, current_time=current_time, debug=False)
                        
                elif self.blackout_when_not_playing:
                    # Only send blackout frame when explicitly enabled
                    blackout_universe = [0] * 512
                    send_artnet(blackout_universe, current_time=current_time, debug=False)
                
                # If not playing and blackout_when_not_playing is False, 
                # don't send any frames to the Art-Net node
                
                # Calculate sleep time to maintain FPS
                await asyncio.sleep(0.01)

                
        except asyncio.CancelledError:
            print("🎬 DMX render loop cancelled")
            raise
        except Exception as e:
            print(f"❌ Error in DMX render loop: {e}")
    
    def _retrieve_dmx_frame(self, current_time: float) -> list:
        """
        Retrieve a single DMX frame from the singleton canvas at the given song time.
        
        This method extracts the DMX universe state from the singleton DMX canvas
        at the precise song time position, ensuring lighting follows the song timeline.
        
        Args:
            current_time: Current song playbook time in seconds
            
        Returns:
            List of 512 DMX channel values (0-255) for the given time
        """
        try:
            # Import here to avoid circular imports
            from .dmx_canvas import DmxCanvas
            
            # Get the singleton DMX canvas instance
            if not DmxCanvas.is_initialized():
                print("⚠️ No DMX canvas singleton initialized")
                return [0] * 512
            
            canvas = DmxCanvas.get_instance()
            
            # Get frame data from canvas at the exact song time
            frame_bytes = canvas.get_frame(current_time)
            if frame_bytes and len(frame_bytes) >= 512:
                # Return the full 512-channel universe
                return list(frame_bytes[:512])
            elif frame_bytes:
                # Pad shorter frames to 512 channels
                frame_list = list(frame_bytes)
                frame_list.extend([0] * (512 - len(frame_list)))
                return frame_list
            
            # No frame data at this time - return blackout
            return [0] * 512
            
        except Exception as e:
            print(f"❌ Error retrieving DMX frame at time {current_time:.3f}s: {e}")
            # Safe fallback on any error
            return [0] * 512
    
    # Playback control methods
    def play(self) -> None:
        """Start playback."""
        self.playback_state.play()
        print(f"▶️ Playback started at {self.playback_state.playback_time:.2f}s")
    
    def pause(self) -> None:
        """Pause playback."""
        self.playback_state.pause()
        print(f"⏸️ Playback paused at {self.playback_state.playback_time:.2f}s")
    
    def stop(self) -> None:
        """Stop playback."""
        self.playback_state.stop()
        print("⏹️ Playback stopped")
    
    def seek(self, time_position: float) -> None:
        """Seek to a specific time position."""
        self.playback_state.seek_to(time_position)
        print(f"🎯 DMX Player seeked to {time_position:.3f}s")

    def get_current_time(self) -> float:
        """Get current playback time."""
        return self.playback_state.get_current_time()
    
    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self.playback_state.is_playing
    
    # Sync methods for WebSocket
    def sync_playback(self, is_playing: bool, current_time: float) -> None:
        """Synchronize playback state from external source (WebSocket)."""
        if is_playing != self.playback_state.is_playing:
            if is_playing:
                # Starting playback - set time and play
                self.playback_state.playback_time = current_time
                self.play()
            else:
                # Pausing playback - set time first, then pause
                self.playback_state.playback_time = current_time
                self.pause()
        else:
            # Just update time if playing state hasn't changed
            if abs(current_time - self.playback_state.get_current_time()) > 0.1:  # Sync if off by more than 100ms
                self.seek(current_time)


# Global DMX player instance
dmx_player = DmxPlayer()
