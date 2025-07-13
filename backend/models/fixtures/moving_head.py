from .fixture_model import FixtureModel
from typing import Optional, Dict, Any
from backend.services.dmx_canvas import DmxCanvas


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
            'pan': self._handle_pan,
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




    def _handle_pan(self, position: float) -> None:
        """
        Handle the pan action for the Moving Head fixture.
        Args:
            position (float): Target position to pan the fixture.
        """
        # TODO: Implement pan movement using fixture configuration
        print(f"  🔄 {self.name}: Pan to position {position} (not yet implemented)")
        raise NotImplementedError("Pan movement not yet implemented")
