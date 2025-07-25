from typing import Optional, Dict, Any
from backend.services.dmx.dmx_canvas import DmxCanvas
from backend.models.position import Position

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
    def channel_names(self) -> Dict[str, int]:
        """Get the channel names to DMX channel mapping from configuration."""
        return self._config.get('channels', {})

    @property
    def position(self) -> Optional[Position]:
        """Get the position of the fixture from configuration."""
        position_config = self._config.get('position', {})
        if not position_config:
            return None
        
        return Position(
            x=position_config.get('x', 0.0),
            y=position_config.get('y', 0.0),
            z=position_config.get('z'),
            label=position_config.get('label')
        )

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
    
    def set_channel_value(self, channel_name: str, value: int, start_time: float = 0.0, duration: Optional[float] = None) -> None:
        """
        Set a specific channel to a value for a given time range.
        Args:
            channel_name (str): Name of the channel (e.g., 'dim', 'red', 'pan').
            value (int): DMX value to set (0-255).
            start_time (float): Start time in seconds.
            duration (Optional[float]): Duration in seconds. If None, uses canvas duration.
        """
        if not self._dmx_canvas:
            raise ValueError("DMX canvas is not set for this fixture.")
        
        channels_config = self._config.get('channels', {})
        if channel_name not in channels_config:
            raise ValueError(f"Channel '{channel_name}' not found in fixture '{self.name}' configuration")
        
        dmx_channel = channels_config[channel_name] - 1  # Convert to 0-based
        end_time = start_time + (duration if duration is not None else self._dmx_canvas.duration)
        
        def channel_value_fn(t: float) -> Dict[int, int]:
            return {dmx_channel: value}
        
        self._dmx_canvas.paint_range(start_time, end_time, channel_value_fn)
        print(f"  💡 {self.name}: Setting channel {channel_name} (DMX {dmx_channel + 1}) to {value} from {start_time:.2f}s to {end_time:.2f}s")

    def fade_channel(self, channel_name: str, from_value: int, to_value: int, start_time: float, duration: float) -> None:
        """
        Fade a channel from one value to another over a given duration.
        Args:
            channel_name (str): Name of the channel (e.g., 'dim', 'red', 'pan').
            from_value (int): Starting DMX value (0-255).
            to_value (int): Ending DMX value (0-255).
            start_time (float): Start time in seconds.
            duration (float): Duration of the fade in seconds.
        """
        if not self._dmx_canvas:
            raise ValueError("DMX canvas is not set for this fixture.")
        
        channels_config = self._config.get('channels', {})
        if channel_name not in channels_config:
            raise ValueError(f"Channel '{channel_name}' not found in fixture '{self.name}' configuration")
        
        dmx_channel = channels_config[channel_name] - 1  # Convert to 0-based
        end_time = start_time + duration
        
        def fade_fn(t: float) -> Dict[int, int]:
            # Calculate progress from 0.0 to 1.0
            progress = (t - start_time) / duration
            progress = max(0.0, min(1.0, progress))  # Clamp to [0, 1]
            
            # Linear interpolation
            current_value = int(from_value + (to_value - from_value) * progress)
            return {dmx_channel: current_value}
        
        self._dmx_canvas.paint_range(start_time, end_time, fade_fn)
        print(f"  🌈 {self.name}: Fading channel {channel_name} (DMX {dmx_channel + 1}) from {from_value} to {to_value} over {duration:.2f}s")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the fixture model to a JSON friendly dictionary representation.
        Returns:
            dict: Dictionary with fixture properties.
        """
        return {
            'id': self._id,
            'name': self._name,
            'fixture_type': self._fixture_type,
            'channels': self._channels,
            'config': self._config,
            'position': self.position.to_dict() if self.position else None
        }

    def __str__(self) -> str:
        """
        String representation of the fixture.
        Returns:
            str: Fixture name and type.
        """
        return f"[{self.fixture_type}|{self.name}]"
