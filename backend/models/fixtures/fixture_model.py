from typing import Optional, Dict, Any
from backend.services.dmx_canvas import DmxCanvas

class FixtureModel:
    def __init__(self, id: str, name: str, fixture_type: str, channels: int, dmx_canvas: Optional[DmxCanvas] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize a fixture model.
        Args:
            id (str): Unique identifier for the fixture.
            name (str): Name of the fixture.
            fixture_type (str): Type of the fixture (e.g., 'parcan', 'moving_head').
            channels (int): Number of DMX channels used by the fixture.
            dmx_canvas (Optional[DmxCanvas]): The DMX canvas instance.
            config (Optional[Dict[str, Any]]): Fixture configuration from fixtures.json.
        """
        self._id = id
        self._name = name
        self._fixture_type = fixture_type
        self._channels = channels
        self._dmx_canvas = dmx_canvas 
        self._config = config or {}
        # Initialize action_handlers if not already set by subclass
        if not hasattr(self, 'action_handlers'):
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
    def dmx_canvas(self):
        """Get the DMX canvas associated with the fixture."""
        return self._dmx_canvas
    
    @dmx_canvas.setter
    def dmx_canvas(self, canvas):
        """Set the DMX canvas for the fixture."""
        self._dmx_canvas = canvas

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
        if self._dmx_canvas is None:
            raise ValueError("DMX canvas is not set for this fixture. Please set it before rendering actions.")
            
        if action in self.action_handlers:
            handler = self.action_handlers[action]
            return handler(**parameters)
        else:
            raise ValueError(f"Action '{action}' is not available for fixture '{self.name}'. Available actions: {self.actions}")
    
    def set_arm(self, state: bool) -> None:
        """
        Set the arm state of the fixture.
        Args:
            state (bool): True to enable, False to disable it (arm channels to 0).
        """
        if not self._dmx_canvas:
            raise ValueError("DMX canvas is not set for this fixture.")
        
        # Get arm configuration from fixtures.json
        arm_config = self._config.get('arm', {})
        channels_config = self._config.get('channels', {})
        
        if not arm_config:
            print(f"⚠️ No arm configuration found for fixture '{self.name}'")
            return
        
        # Set arm channels to appropriate values across the entire canvas duration
        channel_values = {}
        for channel_name, target_value in arm_config.items():
            if channel_name in channels_config:
                dmx_channel = channels_config[channel_name] - 1  # Convert to 0-based
                value = target_value if state else 0
                channel_values[dmx_channel] = value
                
                if state:
                    print(f"  🔧 {self.name}: Setting channel {channel_name} (DMX {dmx_channel + 1}) to {value}")
            else:
                print(f"⚠️ Channel '{channel_name}' not found in fixture '{self.name}' configuration")
        
        # Paint the arm state across the entire canvas duration
        if channel_values:
            # Use paint_range to set values across entire canvas
            def arm_values_fn(t: float) -> Dict[int, int]:
                return channel_values
            
            self._dmx_canvas.paint_range(0.0, self._dmx_canvas.duration, arm_values_fn)
    
    def __str__(self) -> str:
        """
        String representation of the fixture.
        Returns:
            str: Fixture name and type.
        """
        return f"[{self.fixture_type}|{self.name}]"
