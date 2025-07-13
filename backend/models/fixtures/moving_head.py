from .fixture_model import FixtureModel
from typing import Optional, Dict, Any


class MovingHead(FixtureModel):
    def __init__(self, id: str, name: str):
        """
        Initialize an Moving Head fixture.
        Args:
            id (str): Unique identifier for the fixture.
            name (str): Name of the fixture.
        """

        self.action_handlers = {
            'arm': self._handle_arm,
            'pan': self._handle_pan,
        }

        super().__init__(id, name, 'moving_head', 12) # Moving Head uses 12 channels (e.g., pan, tilt, color, etc.)
    
    def render_action(self, action: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        Render a specific action on the Moving Head fixture.
        Args:
            action (str): Action name (e.g., 'pan', 'tilt').
            parameters (dict): Parameters for the action.
        """
        if parameters is None:
            parameters = {}
            
        if action in self.action_handlers:
            handler = self.action_handlers[action]
            return handler(**parameters)
        else:
            raise ValueError(f"Action '{action}' is not available for fixture '{self.name}'. Available actions: {self.actions}")

    def _handle_arm(self) -> dict:
        """
        Handle the arm action for the Moving Head fixture.
        Returns:
            dict: Fixture properties.
        """
        return {
            "id": self.id,
            "name": self.name,
            "type": self.fixture_type,
            "channels": self.channels
        }
    
    def _handle_pan(self, position: float) -> None:
        """
        Handle the pan action for the Moving Head fixture.
        Args:
            position (float): Target position to pan the fixture.
        """
        raise NotImplementedError()
    
    def _handle_flash(self, args: dict) -> None:
        """
        Handle the flash action for the Moving Head fixture.
        Args:
            args (dict): Abstract arguments to the effect.
        """
        raise NotImplementedError()
