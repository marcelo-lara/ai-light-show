from .fixture_model import ActionParameter, ActionModel, FixtureModel
from typing import Optional, Dict, Any
from backend.services.dmx.dmx_canvas import DmxCanvas


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

        self._actions = {
            'arm': ActionModel(
                name='arm',
                handler=self._handle_arm,
                description="Enable/disable the fixture by setting arm channels.",
                parameters=[],
                hidden=True
            ),
            'flash': ActionModel(
                name='flash',
                handler=self._handle_flash,
                description="Triggers a flash effect.",
                parameters=[
                    ActionParameter(name="intensity", value=1.0, description="Flash intensity (0-1)"),
                    ActionParameter(name="duration", value=1.0, description="Flash duration in seconds"),
                    ActionParameter(name="colors", value=['red', 'green', 'blue'], description="Colors to flash")
                ],
                hidden=False
            )
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

    def _handle_flash(self, colors: list[str] = ['red', 'green', 'blue'], start_time: float = 0.0, duration: float = 1.0, intensity: float = 1.0, **kwargs) -> None:
        """
        Handle the flash action for the RGB Parcan fixture.
        Set the specified channels to max intensity, then fade to 0 for a flash effect.
        Args:
            start_time (float): Start time for the flash effect in seconds (default: 0.0).
            duration (float): Duration of the flash fade in seconds (default: 1.0).
            intensity (float): Peak intensity of the flash as a percentage (0.0-1.0, default: 1.0).
            **kwargs: Additional parameters (ignored).
        """
        # If 'white' is specified, set all RGB channels to peak intensity
        if colors == ['white']:
            colors = ['red', 'green', 'blue']
           
        # Convert intensity percentage to DMX value (0-255)
        dmx_intensity = int(intensity * 255)

        # If no channel color is specified, use all RGB channels (usually red)
        if not colors:
            colors = ['red', 'green', 'blue']

        # Set the specified color channels to peak intensity instantly
        for color in colors:
            if color not in self.channel_names:
                print(f"⚠️ {self.name}: No '{color}' channel found for flash effect")
                continue
            # Set the channel value
            self.set_channel_value(color, dmx_intensity, start_time=start_time, duration=0.1)


        # Fade the channels to 0 over the specified duration
        for color in colors:
            if color not in self.channel_names:
                continue
            self.fade_channel(color, dmx_intensity, 0, start_time=start_time + 0.1, duration=duration)

        print(f"  ⚡ {self.name}: Flash effect at {start_time:.2f}s - peak {dmx_intensity}, fade over {duration:.2f}s")
