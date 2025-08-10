from .fixture_model import FixtureModel, ActionModel, ActionParameter
from typing import Optional, Dict, Any
from backend.services.dmx.dmx_canvas import DmxCanvas


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
                    ActionParameter(name="intensity", value=255, description="Flash intensity (0-255)"),
                    ActionParameter(name="duration", value=0.5, description="Flash duration in seconds")
                ],
                hidden=False
            ),
            'seek': ActionModel(
                name='seek',
                handler=self._handle_seek,
                parameters=[
                    ActionParameter(name="target_position", value=(0, 0, 0), description="Target position (x, y, z)"),
                    ActionParameter(name="duration", value=1.0, description="Movement duration in seconds")
                ],
                description="Move the head from the actual position to the target position within a specified travel duration.",
                hidden=False
            ),
            'center_sweep': ActionModel(
                name='center_sweep',
                handler=self._handle_center_sweep,                
                description="A smooth linear pan or tilt movement from point A to B with a dimmer curve that peaks in the middle. This effect is used to highlight a performer or object momentarily during a sweeping motion.",
                parameters=[
                    ActionParameter(name="subject_position", value=(32768, 16384), description="Position of the subject to highlight (x, y)"),
                    ActionParameter(name="start_position", value=(0, 0), description="Starting position of the sweep (x, y)"),
                    ActionParameter(name="duration", value=1.0, description="Duration of the sweep in seconds")
                ],
                hidden=False
            ),
            'searchlight': ActionModel(
                name='searchlight',
                handler=self._handle_searchlight,
                description="A dramatic, wide pan movement imitating old searchlights, sometimes with shutter flicker or strobe for intensity.",
                parameters=[
                    ActionParameter(name="speed", value=1.0, description="Movement speed (0-1)"),
                    ActionParameter(name="duration", value=2.0, description="Duration of the searchlight effect in seconds")
                ],
                hidden=False
            ),
            'flyby': ActionModel(
                name='flyby',
                handler=self._handle_flyby,
                description="A sweeping movement past a subject without stopping, similar to 'center sweep' but with constant dimmer.",
                parameters=[
                    ActionParameter(name="speed", value=1.0, description="Movement speed (0-1)"),
                    ActionParameter(name="duration", value=2.0, description="Duration of the flyby effect in seconds")
                ],
                hidden=False
            ),
            'strobe': ActionModel(
                name='strobe',
                handler=self._handle_strobe,
                description="A rapid flashing effect, often used to create a sense of urgency or excitement.",
                parameters=[
                    ActionParameter(name="intensity", value=255, description="Strobe intensity (0-255)"),
                    ActionParameter(name="duration", value=0.5, description="Strobe duration in seconds")
                ],
                hidden=False
            ),
            'strobe_burst': ActionModel(
                name='strobe_burst',
                handler=self._handle_strobe_burst,
                description="A series of quick, intense flashes, often used to create a dramatic effect.",
                parameters=[
                    ActionParameter(name="intensity", value=255, description="Strobe intensity (0-255)"),
                    ActionParameter(name="duration", value=0.5, description="Strobe duration in seconds"),
                ],
                hidden=False
            ),
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

    def _handle_center_sweep(self, 
                             start_time: float = 0.0, 
                             duration: float = 1.0, 
                             subject_position_x: int = 0, 
                             subject_position_y: int = 0,
                             start_position_x: int = 0,
                             start_position_y: int = 0, 
                             **kwargs) -> None:
        """
        A smooth linear pan or tilt movement from point A to B with a dimmer curve that peaks in the middle. 
        This effect is used to highlight a performer or object momentarily during a sweeping motion.
        
        DMX channel behavior:
            The pan and tilt channels should be set to the start position at start_time, then smoothly transition to the subject position over half the duration,
            and then continue to the opposite side of the subject position for the second half of the duration.
            The dimmer channel should be set to 0 at start_time, then ramp up to peak intensity at the midpoint of the sweep, 
            and then fade back to 0 at the end.
        Args:
            start_time (float): Start time for the sweep in seconds (default: 0.0).
            duration (float): Duration of the sweep in seconds (default: 1.0).
            subject_position_x (int): X position of the subject to highlight (default: 0).
            subject_position_y (int): Y position of the subject to highlight (default: 0).
            start_position_x (int): X position to start the sweep from (default: 0).
            start_position_y (int): Y position to start the sweep from (default: 0).
        """
        # Validate inputs
        if duration <= 0:
            print(f"  ⚠️ {self.name}: Invalid duration {duration}s for center sweep")
            return
        
        # Ensure we have the required channels
        required_channels = ['pan_msb', 'pan_lsb', 'tilt_msb', 'tilt_lsb']
        if not all(ch in self.channel_names for ch in required_channels):
            print(f"  ⚠️ {self.name}: Missing pan/tilt channels for center sweep")
            return
        
        # Check if we have a 'dim' channel
        has_dim_channel = 'dim' in self.channel_names
        
        # Calculate the opposite position (mirror of start position across subject)
        # If start is at (10000, 15000) and subject is at (32768, 16384),
        # then opposite should be at (55536, 17768) - mirrored across subject
        opposite_position_x = 2 * subject_position_x - start_position_x
        opposite_position_y = 2 * subject_position_y - start_position_y
        
        # Clamp positions to valid 16-bit range
        start_position_x = max(0, min(65535, start_position_x))
        start_position_y = max(0, min(65535, start_position_y))
        subject_position_x = max(0, min(65535, subject_position_x))
        subject_position_y = max(0, min(65535, subject_position_y))
        opposite_position_x = max(0, min(65535, opposite_position_x))
        opposite_position_y = max(0, min(65535, opposite_position_y))
        
        # Convert positions to MSB/LSB pairs
        start_pan_msb = (start_position_x >> 8) & 0xFF
        start_pan_lsb = start_position_x & 0xFF
        start_tilt_msb = (start_position_y >> 8) & 0xFF
        start_tilt_lsb = start_position_y & 0xFF
        
        subject_pan_msb = (subject_position_x >> 8) & 0xFF
        subject_pan_lsb = subject_position_x & 0xFF
        subject_tilt_msb = (subject_position_y >> 8) & 0xFF
        subject_tilt_lsb = subject_position_y & 0xFF
        
        opposite_pan_msb = (opposite_position_x >> 8) & 0xFF
        opposite_pan_lsb = opposite_position_x & 0xFF
        opposite_tilt_msb = (opposite_position_y >> 8) & 0xFF
        opposite_tilt_lsb = opposite_position_y & 0xFF
        
        # Calculate timing for the two phases of movement
        half_duration = duration / 2.0
        midpoint_time = start_time + half_duration
        end_time = start_time + duration
        
        # Set initial pan/tilt positions at start_time
        self.set_channel_value('pan_msb', start_pan_msb, start_time=start_time, duration=0)
        self.set_channel_value('pan_lsb', start_pan_lsb, start_time=start_time, duration=0)
        self.set_channel_value('tilt_msb', start_tilt_msb, start_time=start_time, duration=0)
        self.set_channel_value('tilt_lsb', start_tilt_lsb, start_time=start_time, duration=0)
        
        # Phase 1: Move from start position to subject position (first half of duration)
        self.fade_channel('pan_msb', start_pan_msb, subject_pan_msb, start_time, half_duration)
        self.fade_channel('pan_lsb', start_pan_lsb, subject_pan_lsb, start_time, half_duration)
        self.fade_channel('tilt_msb', start_tilt_msb, subject_tilt_msb, start_time, half_duration)
        self.fade_channel('tilt_lsb', start_tilt_lsb, subject_tilt_lsb, start_time, half_duration)
        
        # Phase 2: Move from subject position to opposite position (second half of duration)
        self.fade_channel('pan_msb', subject_pan_msb, opposite_pan_msb, midpoint_time, half_duration)
        self.fade_channel('pan_lsb', subject_pan_lsb, opposite_pan_lsb, midpoint_time, half_duration)
        self.fade_channel('tilt_msb', subject_tilt_msb, opposite_tilt_msb, midpoint_time, half_duration)
        self.fade_channel('tilt_lsb', subject_tilt_lsb, opposite_tilt_lsb, midpoint_time, half_duration)
        
        # Handle dimmer channel if available
        if has_dim_channel:
            # Set dimmer to 0 at start
            self.set_channel_value('dim', 0, start_time=start_time, duration=0)
            
            # Fade dimmer to peak at midpoint (255)
            self.fade_channel('dim', 0, 255, start_time, half_duration)
            
            # Fade dimmer back to 0 at end
            self.fade_channel('dim', 255, 0, midpoint_time, half_duration)
        
        print(f"  🔄 {self.name}: Center sweep from ({start_position_x}, {start_position_y}) to ({subject_position_x}, {subject_position_y}) to ({opposite_position_x}, {opposite_position_y}) over {duration:.2f}s starting at {start_time:.2f}s")

    def _handle_searchlight(self,
                            start_time: float = 0.0, 
                            duration: float = 1.0, 
                            intensity: float = 1.0,
                            radius: int = 0,
                            center_x: int = 0,
                            center_y: int = 0, 
                            **kwargs) -> None:

        """
        A dramatic, wide pan movement imitating old searchlights, sometimes with shutter flicker or strobe for intensity.
        The position of pan and tilt should be a circle around the center point (center_x, center_y) with a specified radius.
        The shutter channel should be always open (255) during the searchlight effect.
        The dim channel should be set to the relative intensity (0-255 * intensity).
        This is a placeholder for future implementation.
        Args:
            start_time (float): Start time for the searchlight in seconds (default: 0.0).
            duration (float): Duration of the searchlight in seconds (default: 1.0).
        """        
        # Currently, this method does nothing but can be extended later
        print(f"  ⚠️ {self.name}: Searchlight from ({center_x}, {center_y}) radius ({radius}) over {duration:.2f}s starting at {start_time:.2f}s")

    def _handle_flyby(self, 
                        start_time: float = 0.0, 
                        duration: float = 1.0, 
                        subject_position_x: int = 0, 
                        subject_position_y: int = 0,
                        start_position_x: int = 0,
                        start_position_y: int = 0,
                        **kwargs) -> None:
        """
        The beam sweeps past a subject without stopping, similar to "center sweep" but with constant dimmer
        This is a placeholder for future implementation.
        Args:
            start_time (float): Start time for the searchlight in seconds (default: 0.0).
            duration (float): Duration of the searchlight in seconds (default: 1.0).
        """
        # Currently, this method does nothing but can be extended later
        print(f"  ⚠️ {self.name}: Flyby from ({start_position_x}, {start_position_y}) to ({subject_position_x}, {subject_position_y}) over {duration:.2f}s starting at {start_time:.2f}s")

    def _handle_strobe(self,
                        start_time: float = 0.0,
                        duration: float = 1.0,
                        intensity: float = 1.0,
                        frequency: float = 1.0, 
                        **kwargs) -> None:
        """
        Handle the strobe effect for the Moving Head fixture.
        Creates a strobe effect by rapidly switching the shutter channel on and off.
        DMX channel behavior:
            The 'shutter' channel is used to create the strobe effect: alternating 0 (closed) and 255 (open) at the specified frequency (specified in Hz).
            The 'dim' channel is set to the relative intensity (0-255 * intensity).
        Args:
            start_time (float): Start time for the strobe effect in seconds (default: 0.0).
            duration (float): Duration of the strobe effect in seconds (default: 1.0).
            intensity (float): Intensity of the strobe effect (0.0 to 1.0, default: 1.0).
            frequency (float): Frequency of the strobe effect in Hz (default: 1.0).
        """
        # Check if we have a 'shutter' channel
        if 'shutter' not in self.channel_names:
            print(f"⚠️ {self.name}: No 'shutter' channel found for strobe effect")
            return
        
        # Convert intensity to DMX value (0-255) for the dim channel
        dmx_intensity = int(intensity * 255)
        
        # Set the dim channel to the specified intensity
        if 'dim' in self.channel_names:
            self.set_channel_value('dim', dmx_intensity, start_time=start_time, duration=duration)
        
        # Calculate period (time for one on/off cycle)
        if frequency <= 0:
            print(f"⚠️ {self.name}: Invalid frequency {frequency}Hz for strobe effect")
            return
            
        period = 1.0 / frequency  # Time for one complete cycle (on + off)
        half_period = period / 2.0  # Time for each on/off state
        
        # Create strobe effect by setting rapid on/off states
        current_time = start_time
        end_time = start_time + duration
        
        # If frequency is too high or duration too short, just set a constant value
        if period < 0.01 or duration < 0.01:  # Less than 10ms period or duration
            # For very high frequency, set shutter to open (255)
            self.set_channel_value('shutter', 255, start_time=start_time, duration=duration)
            print(f"  ⚡ {self.name}: High-frequency strobe effect at {start_time:.2f}s for {duration:.2f}s with intensity {intensity:.2f} ({dmx_intensity})")
            return
        
        # Create individual strobe flashes
        flash_count = 0
        while current_time < end_time:
            # Set shutter to "closed" (0) for the first half of the period
            self.set_channel_value('shutter', 0, start_time=current_time, duration=half_period)
            
            # Set shutter to "open" (255) for the second half
            self.set_channel_value('shutter', 255, start_time=current_time + half_period, duration=half_period)
            
            # Move to next cycle
            current_time += period
            flash_count += 1
            
            # Safety check to prevent infinite loops
            if flash_count > 10000:
                break
        
        print(f"  ⚡ {self.name}: Strobe effect at {start_time:.2f}s for {duration:.2f}s with intensity {intensity:.2f} ({dmx_intensity}) and frequency {frequency:.2f}Hz ({flash_count} flashes)")

    def _handle_strobe_burst(self,
                             start_time: float = 0.0,
                             duration: float = 1.0,
                             start_intensity: float = 0.0,
                             start_frequency: float = 0.0,
                             end_frequency: float = 1.0,
                             end_intensity: float = 1.0, 
                             **kwargs) -> None:
        """
        Handle the strobe burst effect for the Moving Head fixture.
        The strobe burst is a rapid series of flashes that can vary in intensity and frequency.
        Frequently used in drops or climactic moments in EDM.
        DMX channel behavior:
            The 'shutter' channel is used to create the strobe effect: alternating 0 (closed) and 255 (open) starting at the start-frequency (specified in Hz) and ramps to end at the end-frequency.
            The 'dim' channel is set to the relative start-intensity (0-255 * intensity) and ramps to the end-intensity over the duration.
        Args:
            start_time (float): Start time for the strobe burst in seconds (default: 0.0).
            duration (float): Duration of the strobe burst in seconds (default: 1.0).
            start_intensity (float): Initial intensity of the strobe burst (0.0 to 1.0, default: 0.0).
            start_frequency (float): Initial frequency of the strobe burst in Hz (default: 0.0).
            end_frequency (float): Final frequency of the strobe burst in Hz (default: 1.0).
            end_intensity (float): Final intensity of the strobe burst (0.0 to 1.0, default: 1.0).
        """
        # Check if we have a 'shutter' channel
        if 'shutter' not in self.channel_names:
            print(f"⚠️ {self.name}: No 'shutter' channel found for strobe burst effect")
            return
        
        # Validate parameters
        if duration <= 0:
            print(f"⚠️ {self.name}: Invalid duration {duration}s for strobe burst effect")
            return
            
        # Ensure frequency values are valid
        start_frequency = max(0.0, start_frequency)
        end_frequency = max(0.0, end_frequency)
        
        # Ensure intensity values are in valid range
        start_intensity = max(0.0, min(1.0, start_intensity))
        end_intensity = max(0.0, min(1.0, end_intensity))
        
        # Calculate end time
        end_time = start_time + duration
        
        # Handle dimmer channel if available
        if 'dim' in self.channel_names:
            start_dmx_intensity = int(start_intensity * 255)
            end_dmx_intensity = int(end_intensity * 255)
            self.fade_channel('dim', start_dmx_intensity, end_dmx_intensity, start_time, duration)

        # For very short durations or invalid parameters, just set a constant value
        if duration < 0.01 or (start_frequency <= 0 and end_frequency <= 0):
            # Calculate average intensity
            avg_intensity = (start_intensity + end_intensity) / 2.0
            dmx_intensity = int(avg_intensity * 255)
            self.set_channel_value('shutter', dmx_intensity, start_time=start_time, duration=duration)
            print(f"  ⚡ {self.name}: Short strobe burst effect at {start_time:.2f}s for {duration:.2f}s with avg intensity {avg_intensity:.2f} ({dmx_intensity})")
            return
        
        # Create the strobe burst effect by dynamically changing frequency and intensity over time
        current_time = start_time
        total_flashes = 0
        
        # We'll create the effect in small time segments to approximate the ramping
        time_segment = 0.05  # 50ms segments for smooth transitions
        segment_count = int(duration / time_segment)
        
        # If we have very few segments, adjust time_segment
        if segment_count < 10:
            time_segment = duration / 10.0
            segment_count = 10
            
        for i in range(segment_count):
            # Calculate progress (0.0 to 1.0) for this segment
            progress = i / (segment_count - 1) if segment_count > 1 else 0.0
            
            # Interpolate frequency and intensity for this segment
            current_frequency = start_frequency + (end_frequency - start_frequency) * progress
            current_intensity = start_intensity + (end_intensity - start_intensity) * progress
            
            # Calculate period for this segment
            if current_frequency <= 0:
                # If frequency is 0 or negative, just set the intensity and move on
                dmx_intensity = int(current_intensity * 255)
                segment_start = current_time
                segment_end = min(current_time + time_segment, end_time)
                self.set_channel_value('shutter', dmx_intensity, start_time=segment_start, duration=segment_end - segment_start)
                current_time = segment_end
                continue
                
            period = 1.0 / current_frequency
            half_period = period / 2.0
            
            # For very high frequencies, just set a constant value for this segment
            if period < 0.01:  # Less than 10ms period
                dmx_intensity = int(current_intensity * 255)
                segment_start = current_time
                segment_end = min(current_time + time_segment, end_time)
                self.set_channel_value('shutter', dmx_intensity, start_time=segment_start, duration=segment_end - segment_start)
                current_time = segment_end
                continue
            
            # Create strobe flashes for this time segment
            segment_end_time = min(current_time + time_segment, end_time)
            flash_count = 0
            
            while current_time < segment_end_time and flash_count < 1000:  # Safety limit
                # Set shutter to "closed" (0) for the first half of the period
                self.set_channel_value('shutter', 0, start_time=current_time, duration=half_period)
                
                # Set shutter to "open" (dmx_intensity) for the second half
                dmx_intensity = 255 # Strobe is usually full open on shutter
                self.set_channel_value('shutter', dmx_intensity, start_time=current_time + half_period, duration=half_period)
                
                # Move to next cycle
                current_time += period
                flash_count += 1
                total_flashes += 1
                
                # Break if we've reached the end time
                if current_time >= end_time:
                    break
            
            # Break if we've reached the end time
            if current_time >= end_time:
                break
        
        print(f"  ⚡ {self.name}: Strobe burst effect at {start_time:.2f}s for {duration:.2f}s with intensity ramp from {start_intensity:.2f} to {end_intensity:.2f} and frequency ramp from {start_frequency:.2f}Hz to {end_frequency:.2f}Hz ({total_flashes} total flashes)")

    def _handle_seek(self, start_time: float = 0.0, duration: float = 1.0, pos_x: int = 0, pos_y: int = 0, **kwargs) -> None:
        """
        Move the head from the actual position to the target position within a specified travel duration.
        Args:
            start_time (float): Time to start the movement (seconds).
            duration (float): Time to complete the movement (seconds).
            pos_x (int): Target X position (pan) as 16-bit value (0-65535).
            pos_y (int): Target Y position (tilt) as 16-bit value (0-65535).
        Note:
            The pan/tilt values are maintained after the action completes until the next seek
            action or the end of the song.
        """
        # Ensure valid 16-bit values
        pos_x = max(0, min(65535, int(pos_x)))
        pos_y = max(0, min(65535, int(pos_y)))
        
        # Convert 16-bit positions to MSB/LSB pairs
        pan_msb = (pos_x >> 8) & 0xFF
        pan_lsb = pos_x & 0xFF
        tilt_msb = (pos_y >> 8) & 0xFF
        tilt_lsb = pos_y & 0xFF
        
        # Get the maximum time value for the DMX canvas to maintain values until the end of the song
        # Using a very large integer (24 hours in seconds) instead of infinity to avoid conversion errors
        max_time = 86400  # 24 hours in seconds, practically the end of any song
        
        # If duration is very short, use direct positioning
        if duration < 0.1:
            # Set pan channels and maintain values indefinitely
            self.set_channel_value('pan_msb', pan_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time, duration=max_time)
            
            # Set tilt channels and maintain values indefinitely
            self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time, duration=max_time)
            
            print(f"  🔄 {self.name}: Instant seek to position ({pos_x}, {pos_y}) at {start_time:.2f}s (values maintained)")
        else:
            # For longer durations, use fading for smooth movement
            try:
                # Get current position values if available
                from backend.services.dmx.dmx_dispatcher import get_channel_value
                
                # Get the DMX channels for each component
                channels = self._config.get('channels', {})
                pan_msb_ch = channels.get('pan_msb')
                pan_lsb_ch = channels.get('pan_lsb')
                tilt_msb_ch = channels.get('tilt_msb')
                tilt_lsb_ch = channels.get('tilt_lsb')
                
                # Check if we have all necessary channel mappings
                if all(x is not None for x in [pan_msb_ch, pan_lsb_ch, tilt_msb_ch, tilt_lsb_ch]):
                    # Get current values (convert from 1-based to 0-based)
                    current_pan_msb = get_channel_value(pan_msb_ch - 1)
                    current_pan_lsb = get_channel_value(pan_lsb_ch - 1)
                    current_tilt_msb = get_channel_value(tilt_msb_ch - 1)
                    current_tilt_lsb = get_channel_value(tilt_lsb_ch - 1)
                    
                    # Fade pan channels during the movement
                    self.fade_channel('pan_msb', current_pan_msb, pan_msb, start_time, duration)
                    self.fade_channel('pan_lsb', current_pan_lsb, pan_lsb, start_time, duration)
                    
                    # Fade tilt channels during the movement
                    self.fade_channel('tilt_msb', current_tilt_msb, tilt_msb, start_time, duration)
                    self.fade_channel('tilt_lsb', current_tilt_lsb, tilt_lsb, start_time, duration)
                    
                    # After the fade completes, maintain the final values indefinitely
                    self.set_channel_value('pan_msb', pan_msb, start_time=start_time + duration, duration=max_time)
                    self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time + duration, duration=max_time)
                    self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time + duration, duration=max_time)
                    self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time + duration, duration=max_time)
                    
                    print(f"  🔄 {self.name}: Smooth seek to position ({pos_x}, {pos_y}) over {duration:.2f}s starting at {start_time:.2f}s (values maintained)")
                    return
            except (KeyError, AttributeError, Exception) as e:
                # If we can't get current values, fall back to direct setting
                print(f"  ⚠️ {self.name}: Error getting current position, falling back to direct setting: {e}")
                
            # Fallback: directly set target position with no transition and maintain indefinitely
            self.set_channel_value('pan_msb', pan_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('pan_lsb', pan_lsb, start_time=start_time, duration=max_time)
            self.set_channel_value('tilt_msb', tilt_msb, start_time=start_time, duration=max_time)
            self.set_channel_value('tilt_lsb', tilt_lsb, start_time=start_time, duration=max_time)
            
            print(f" FALLBACK 🔄 {self.name}: Direct seek to position ({pos_x}, {pos_y}) at {start_time:.2f}s (values maintained)")
