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




    def _handle_seek(self, start_time: float = 0.0, duration: float = 1.0, pos_x: int = 0, pos_y: int = 0) -> None:
        """
        Handle the seek action for the Moving Head fixture.
        Args:
            start_time (float): Time to start the movement (seconds).
            duration (float): Time to complete the movement (seconds).
            pos_x (int): Target X position (pan) as 16-bit value (0-65535).
            pos_y (int): Target Y position (tilt) as 16-bit value (0-65535).
        """
        # Ensure valid 16-bit values
        pos_x = max(0, min(65535, int(pos_x)))
        pos_y = max(0, min(65535, int(pos_y)))
        
        # Convert 16-bit positions to MSB/LSB pairs
        pan_msb = (pos_x >> 8) & 0xFF
        pan_lsb = pos_x & 0xFF
        tilt_msb = (pos_y >> 8) & 0xFF
        tilt_lsb = pos_y & 0xFF
        
        # If duration is very short, use direct positioning
        if duration < 0.1:
            # Set pan channels
            self.set_channel_value('pan_msb', pan_msb, start_time=start_time)
            self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time)
            
            # Set tilt channels
            self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time)
            self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time)
            
            print(f"  🔄 {self.name}: Instant seek to position ({pos_x}, {pos_y}) at {start_time:.2f}s")
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
                    
                    # Fade pan channels
                    self.fade_channel('pan_msb', current_pan_msb, pan_msb, start_time, duration)
                    self.fade_channel('pan_lsb', current_pan_lsb, pan_lsb, start_time, duration)
                    
                    # Fade tilt channels
                    self.fade_channel('tilt_msb', current_tilt_msb, tilt_msb, start_time, duration)
                    self.fade_channel('tilt_lsb', current_tilt_lsb, tilt_lsb, start_time, duration)
                    
                    print(f"  🔄 {self.name}: Smooth seek to position ({pos_x}, {pos_y}) over {duration:.2f}s starting at {start_time:.2f}s")
                    return
            except (KeyError, AttributeError, Exception) as e:
                # If we can't get current values, fall back to direct setting
                print(f"  ⚠️ {self.name}: Error getting current position, falling back to direct setting: {e}")
                
            # Fallback: directly set target position with no transition
            self.set_channel_value('pan_msb', pan_msb, start_time=start_time)
            self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time)
            self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time)
            self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time)
            
            print(f"  🔄 {self.name}: Direct seek to position ({pos_x}, {pos_y}) at {start_time:.2f}s")
