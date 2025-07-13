from .fixture_model import FixtureModel


class RgbParcan(FixtureModel):
    def __init__(self, id: str, name: str):
        """
        Initialize an RGB Parcan fixture.
        Args:
            id (str): Unique identifier for the fixture.
            name (str): Name of the fixture.
        """

        self.action_handlers = {
            'arm': self._handle_arm,
            'flash': self._handle_flash,
        }

        super().__init__(id, name, 'parcan', 3)  # RGB Parcan uses 3 channels (R, G, B)
    
    def _handle_arm(self) -> dict:
        """
        Handle the arm action for the RGB Parcan fixture.
        Returns:
            dict: Fixture properties.
        """
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
