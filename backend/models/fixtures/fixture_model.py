from typing import Optional, Dict, Any


class FixtureModel:
    def __init__(self, id: str, name: str, fixture_type: str, channels: int):
        """
        Initialize a fixture model.
        Args:
            id (str): Unique identifier for the fixture.
            name (str): Name of the fixture.
            fixture_type (str): Type of the fixture (e.g., 'parcan', 'moving_head').
            channels (int): Number of DMX channels used by the fixture.
        """
        self._id = id
        self._name = name
        self._fixture_type = fixture_type
        self._channels = channels
        self.action_handlers = {}  # Should be overridden by subclasses
    
    @property
    def id(self) -> str:
        """Get the fixture ID."""
        return self._id
    
    @property
    def name(self) -> str:
        """Get the fixture name."""
        return self._name
    
    @property
    def fixture_type(self) -> str:
        """Get the fixture type."""
        return self._fixture_type
    
    @property
    def channels(self) -> int:
        """Get the number of channels."""
        return self._channels
    
    @property
    def actions(self):
        """
        Get the actions associated with the fixture (derived from handlers).
        Returns:
            list: List of available action names.
        """
        return list(self.action_handlers.keys())
    
    def render_action(self, action: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        """
        Render a specific action on the fixture.
        Args:
            action (str): Action name (e.g., 'flash', 'fade').
            parameters (dict): Parameters for the action.
        """
        if parameters is None:
            parameters = {}
            
        if action in self.action_handlers:
            handler = self.action_handlers[action]
            return handler(**parameters)
        else:
            raise ValueError(f"Action '{action}' is not available for fixture '{self.name}'. Available actions: {self.actions}")
    
    def set_color(self, color: tuple) -> None:
        """
        Set the color of the fixture.
        Args:
            color (tuple): RGB color values as a tuple (R, G, B).
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def set_channel_value(self, channel: int, value: int) -> None:
        """
        Set a specific DMX channel value.
        Args:
            channel (int): DMX channel number (0-511).
            value (int): Value to set (0-255).
        """
        raise NotImplementedError("This method should be implemented by subclasses.")
    
    def get_channel(self, channel: str) -> int:
        """
        Get the DMX channel number of given channel .
        Args:
            channel (int): DMX channel number (0-511).
        Returns:
            int: Value of the specified channel (0-255).
        """
        raise NotImplementedError("This method should be implemented by subclasses.")

    def __str__(self) -> str:
        """
        String representation of the fixture.
        Returns:
            str: Fixture name and type.
        """
        return f"[{self.fixture_type}|{self.name}]"
