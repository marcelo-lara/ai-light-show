from .fixture_model import FixtureModel
from typing import Optional
from backend.services.dmx_canvas import DmxCanvas


class RgbParcan(FixtureModel):
    def __init__(self, id: str, name: str, dmx_canvas: Optional[DmxCanvas] = None):
        """
        Initialize an RGB Parcan fixture.
        Args:
            id (str): Unique identifier for the fixture.
            name (str): Name of the fixture.
            dmx_canvas (Optional[DmxCanvas]): The DMX canvas instance.
        """

        self.action_handlers = {
            'arm': self._handle_arm,
            'flash': self._handle_flash,
        }

        super().__init__(id, name, 'parcan', 3, dmx_canvas)  # RGB Parcan uses 3 channels (R, G, B)
    
    def _handle_arm(self) -> dict:
        """
        Handle the arm action for the RGB Parcan fixture.
        Returns:
            dict: Fixture properties.
        """
        # Example of using the DMX canvas
        if self.dmx_canvas:
            print(f"  🎛️ {self.name} accessing DMX canvas (duration: {self.dmx_canvas.duration:.2f}s)")
        
        return {
            "id": self.id,
            "name": self.name,
            "type": self.fixture_type,
            "channels": self.channels
        }
    
    def _handle_flash(self, args: dict) -> None:
        """
        Handle the flash action for the RGB Parcan fixture.
        Args:
            args (dict): Abstract arguments to the effect.
        """
        raise NotImplementedError()
