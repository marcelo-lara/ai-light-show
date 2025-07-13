from .fixture_model import FixtureModel
from typing import Optional, Dict, Any
from backend.services.dmx_canvas import DmxCanvas


class RgbParcan(FixtureModel):
    def __init__(self, id: str, name: str, dmx_canvas: Optional[DmxCanvas] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize an RGB Parcan fixture.
        Args:
            id (str): Unique identifier for the fixture.
            name (str): Name of the fixture.
            dmx_canvas (Optional[DmxCanvas]): The DMX canvas instance.
            config (Optional[Dict[str, Any]]): Fixture configuration from fixtures.json.
        """

        self.action_handlers = {
            'arm': self._handle_arm,
            'flash': self._handle_flash,
        }

        super().__init__(id, name, 'parcan', 3, dmx_canvas, config)  # RGB Parcan uses 3 channels (R, G, B)
    
    def _handle_arm(self) -> dict:
        """
        Handle the arm action for the RGB Parcan fixture.
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
        Handle the flash action for the RGB Parcan fixture.
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
