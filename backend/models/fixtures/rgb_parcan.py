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
    
    def _handle_flash(self, args: dict) -> None:
        """
        Handle the flash action for the RGB Parcan fixture.
        Args:
            args (dict): Abstract arguments to the effect.
        """
        # TODO: Implement flash effect using fixture configuration
        print(f"  ⚡ {self.name}: Flash effect (not yet implemented)")
        raise NotImplementedError("Flash effect not yet implemented")
