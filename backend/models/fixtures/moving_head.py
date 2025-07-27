from .fixture_model import FixtureModel
from typing import Optional, Dict, Any
from backend.services.dmx.dmx_canvas import DmxCanvas


class MovingHead(FixtureModel):
    def __init__(self, id: str, name: str, dmx_canvas: Optional[DmxCanvas] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an Moving Head fixture.
        Args:
            id (str): Unique identifier for the fixture.
            name (str): Name of the fixture.
            dmx_canvas (Optional[DmxCanvas]): The DMX canvas instance.
            config (Optional[Dict[str, Any]]): Fixture configuration from fixtures.json.
        """

        self.action_handlers = {
            'arm': self._handle_arm,
            'flash': self._handle_flash,
            'seek': self._handle_seek,
            'center_sweep': self._handle_center_sweep,
            'searchlight': self._handle_searchlight,
            'flyby': self._handle_flyby,
            'strobe': self._handle_strobe,
            'strobe_burst': self._handle_strobe_burst,
        }

        super().__init__(id, name, 'moving_head', 12, dmx_canvas, config) # Moving Head uses 12 channels (e.g., pan, tilt, color, etc.)
    
    def _handle_arm(self) -> dict:
        """
        Handle the arm action for the Moving Head fixture.
        Returns:
            dict: Fixture properties.
        """
        # Use the base class set_arm method with configuration from fixtures.json
        self.set_arm(True)
        
        return {
            "id": self.id,
            "name": self.name,
            "type": self.fixture_type,
            "channels": self.channels
        }

    def _handle_flash(self, start_time: float = 0.0, duration: float = 1.0, intensity: float = 1.0, **kwargs) -> None:
        """
        Handle the flash action for the Moving Head fixture.
        Set the 'dim' channel to max intensity, then fade to 0 for a flash effect.
        Args:
            start_time (float): Start time for the flash effect in seconds (default: 0.0).
            duration (float): Duration of the flash fade in seconds (default: 1.0).
            intensity (float): Peak intensity of the flash as a percentage (0.0-1.0, default: 1.0).
            **kwargs: Additional parameters (ignored).
        """
        # Check if we have a 'dim' channel
        if 'dim' not in self.channel_names:
            print(f"⚠️ {self.name}: No 'dim' channel found for flash effect")
            return
        
        # Convert intensity percentage to DMX value (0-255)
        dmx_intensity = int(intensity * 255)
        
        # Set the dim channel to peak intensity instantly
        self.set_channel_value('dim', dmx_intensity, start_time=start_time, duration=0.1)
        
        # Fade the dim channel to 0 over the specified duration
        self.fade_channel('dim', dmx_intensity, 0, start_time=start_time + 0.1, duration=duration)

        print(f"  ⚡ {self.name}: Flash effect at {start_time:.2f}s - peak {dmx_intensity}, fade over {duration:.2f}s")

    def _handle_center_sweep(self, 
                             start_time: float = 0.0, 
                             duration: float = 1.0, 
                             subject_position_x: int = 0, 
                             subject_position_y: int = 0,
                             start_position_x: int = 0,
                             start_position_y: int = 0) -> None:
        """
        A smooth linear pan or tilt movement from point A to B with a dimmer curve that peaks in the middle. 
        Often used to highlight a performer or object momentarily during a sweeping motion.
        Args:
            start_time (float): Start time for the sweep in seconds (default: 0.0).
            duration (float): Duration of the sweep in seconds (default: 1.0).
        """
        # Currently, this method does nothing but can be extended later
        print(f"  ⚠️ {self.name}: Center sweep from ({start_position_x}, {start_position_y}) to ({subject_position_x}, {subject_position_y}) over {duration:.2f}s starting at {start_time:.2f}s")

    def _handle_searchlight(self,
                            start_time: float = 0.0, 
                            duration: float = 1.0, 
                            radius: int = 0,
                            center_x: int = 0,
                            center_y: int = 0) -> None:

        """
        A dramatic, wide pan movement imitating old searchlights, sometimes with shutter flicker or strobe for intensity.
        This is a placeholder for future implementation.
        Args:
            start_time (float): Start time for the searchlight in seconds (default: 0.0).
            duration (float): Duration of the searchlight in seconds (default: 1.0).
        """        
        # Currently, this method does nothing but can be extended later
        print(f"  ⚠️ {self.name}: Searchlight from ({center_x}, {center_y}) radius ({radius}) over {duration:.2f}s starting at {start_time:.2f}s")

    def _handle_flyby(self, 
                        start_time: float = 0.0, 
                        duration: float = 1.0, 
                        subject_position_x: int = 0, 
                        subject_position_y: int = 0,
                        start_position_x: int = 0,
                        start_position_y: int = 0) -> None:
        """
        The beam sweeps past a subject without stopping, similar to "center sweep" but with constant dimmer
        This is a placeholder for future implementation.
        Args:
            start_time (float): Start time for the searchlight in seconds (default: 0.0).
            duration (float): Duration of the searchlight in seconds (default: 1.0).
        """
        # Currently, this method does nothing but can be extended later
        print(f"  ⚠️ {self.name}: Flyby from ({start_position_x}, {start_position_y}) to ({subject_position_x}, {subject_position_y}) over {duration:.2f}s starting at {start_time:.2f}s")

    def _handle_strobe(self,
                        start_time: float = 0.0,
                        duration: float = 1.0,
                        intensity: float = 1.0,
                        frequency: float = 1.0) -> None:
        """
        Handle the strobe effect for the Moving Head fixture.
        Args:
            start_time (float): Start time for the strobe effect in seconds (default: 0.0).
            duration (float): Duration of the strobe effect in seconds (default: 1.0).
            intensity (float): Intensity of the strobe effect (0.0 to 1.0, default: 1.0).
            frequency (float): Frequency of the strobe effect in Hz (default: 1.0).
        """
        # Currently, this method does nothing but can be extended later
        print(f"  ⚠️ {self.name}: Strobe effect at {start_time:.2f}s for {duration:.2f}s with intensity {intensity:.2f} and frequency {frequency:.2f}Hz")

    def _handle_strobe_burst(self,
                             start_time: float = 0.0,
                             duration: float = 1.0,
                             start_intensity: float = 0.0,
                             start_frequency: float = 0.0,
                             end_frequency: float = 1.0,
                             end_intensity: float = 1.0) -> None:
        """
        Handle the strobe burst effect for the Moving Head fixture.
        The strobe burst is a rapid series of flashes that can vary in intensity and frequency.
        Frequently used in drops or climactic moments in EDM.
        Args:
            start_time (float): Start time for the strobe burst in seconds (default: 0.0).
            duration (float): Duration of the strobe burst in seconds (default: 1.0).
            start_intensity (float): Initial intensity of the strobe burst (0.0 to 1.0, default: 0.0).
            start_frequency (float): Initial frequency of the strobe burst in Hz (default: 0.0).
            end_frequency (float): Final frequency of the strobe burst in Hz (default: 1.0).
            end_intensity (float): Final intensity of the strobe burst (0.0 to 1.0, default: 1.0).
        """
        # Currently, this method does nothing but can be extended later
        print(f"  ⚠️ {self.name}: Strobe burst effect at {start_time:.2f}s for {duration:.2f}s with intensity {start_intensity:.2f} and frequency ramp from {start_frequency:.2f}Hz to {end_frequency:.2f}Hz ending at intensity {end_intensity:.2f}")

    def _handle_seek(self, start_time: float = 0.0, duration: float = 1.0, pos_x: int = 0, pos_y: int = 0) -> None:
        """
        Handle the seek action for the Moving Head fixture.
        Args:
            start_time (float): Time to start the movement (seconds).
            duration (float): Time to complete the movement (seconds).
            pos_x (int): Target X position (pan) as 16-bit value (0-65535).
            pos_y (int): Target Y position (tilt) as 16-bit value (0-65535).
        Note:
            The pan/tilt values are maintained after the action completes until the next seek
            action or the end of the song.
        """
        # Ensure valid 16-bit values
        pos_x = max(0, min(65535, int(pos_x)))
        pos_y = max(0, min(65535, int(pos_y)))
        
        # Convert 16-bit positions to MSB/LSB pairs
        pan_msb = (pos_x >> 8) & 0xFF
        pan_lsb = pos_x & 0xFF
        tilt_msb = (pos_y >> 8) & 0xFF
        tilt_lsb = pos_y & 0xFF
        
        # Get the maximum time value for the DMX canvas to maintain values until the end of the song
        # Using a very large integer (24 hours in seconds) instead of infinity to avoid conversion errors
        max_time = 86400  # 24 hours in seconds, practically the end of any song
        
        # If duration is very short, use direct positioning
        if duration < 0.1:
            # Set pan channels and maintain values indefinitely
            self.set_channel_value('pan_msb', pan_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time, duration=max_time)
            
            # Set tilt channels and maintain values indefinitely
            self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time, duration=max_time)
            
            print(f"  🔄 {self.name}: Instant seek to position ({pos_x}, {pos_y}) at {start_time:.2f}s (values maintained)")
        else:
            # For longer durations, use fading for smooth movement
            try:
                # Get current position values if available
                from backend.services.dmx.dmx_dispatcher import get_channel_value
                
                # Get the DMX channels for each component
                channels = self._config.get('channels', {})
                pan_msb_ch = channels.get('pan_msb')
                pan_lsb_ch = channels.get('pan_lsb')
                tilt_msb_ch = channels.get('tilt_msb')
                tilt_lsb_ch = channels.get('tilt_lsb')
                
                # Check if we have all necessary channel mappings
                if all(x is not None for x in [pan_msb_ch, pan_lsb_ch, tilt_msb_ch, tilt_lsb_ch]):
                    # Get current values (convert from 1-based to 0-based)
                    current_pan_msb = get_channel_value(pan_msb_ch - 1)
                    current_pan_lsb = get_channel_value(pan_lsb_ch - 1)
                    current_tilt_msb = get_channel_value(tilt_msb_ch - 1)
                    current_tilt_lsb = get_channel_value(tilt_lsb_ch - 1)
                    
                    # Fade pan channels during the movement
                    self.fade_channel('pan_msb', current_pan_msb, pan_msb, start_time, duration)
                    self.fade_channel('pan_lsb', current_pan_lsb, pan_lsb, start_time, duration)
                    
                    # Fade tilt channels during the movement
                    self.fade_channel('tilt_msb', current_tilt_msb, tilt_msb, start_time, duration)
                    self.fade_channel('tilt_lsb', current_tilt_lsb, tilt_lsb, start_time, duration)
                    
                    # After the fade completes, maintain the final values indefinitely
                    self.set_channel_value('pan_msb', pan_msb, start_time=start_time + duration, duration=max_time)
                    self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time + duration, duration=max_time)
                    self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time + duration, duration=max_time)
                    self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time + duration, duration=max_time)
                    
                    print(f"  🔄 {self.name}: Smooth seek to position ({pos_x}, {pos_y}) over {duration:.2f}s starting at {start_time:.2f}s (values maintained)")
                    return
            except (KeyError, AttributeError, Exception) as e:
                # If we can't get current values, fall back to direct setting
                print(f"  ⚠️ {self.name}: Error getting current position, falling back to direct setting: {e}")
                
            # Fallback: directly set target position with no transition and maintain indefinitely
            self.set_channel_value('pan_msb', pan_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time, duration=max_time)
            self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time, duration=max_time)
            
            print(f" FALLBACK 🔄 {self.name}: Direct seek to position ({pos_x}, {pos_y}) at {start_time:.2f}s (values maintained)")
