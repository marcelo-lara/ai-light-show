"""
DMX Controller for AI Light Show.

Provides DMX512 control via Art-Net protocol with proper type hints
and error handling for improved reliability and IntelliSense support.
"""

from time import perf_counter
import socket
from typing import List, Optional, Dict, Any
from .types import ChannelValue, DMXUniverse
from .core.validation import validate_dmx_channel, validate_dmx_value
from .core.exceptions import DMXError, NetworkError

# DMX Constants
DMX_CHANNELS: int = 512
FPS: int = 60
ARTNET_PORT: int = 6454
ARTNET_IP: str = "192.168.1.221"  # real 192.168.1.221
ARTNET_UNIVERSE: int = 0

# DMX State
dmx_universe: List[ChannelValue] = [0] * DMX_CHANNELS
last_artnet_send: float = 0.0
last_packet: List[ChannelValue] = [0] * DMX_CHANNELS


def set_channel(ch: int, val: ChannelValue) -> bool:
    """
    Set a DMX channel value.
    
    Args:
        ch: DMX channel number (1-512)
        val: DMX value (0-255)
        
    Returns:
        True if successful
        
    Raises:
        DMXError: If channel or value is invalid
    """
    try:
        validate_dmx_channel(ch)
        validate_dmx_value(val)
        
        dmx_universe[ch - 1] = val
        return True
        
    except ValueError as e:
        raise DMXError(f"Invalid channel/value: {e}", channel=ch, value=val)


def set_channels(channels: Dict[int, ChannelValue]) -> bool:
    """
    Set multiple DMX channels at once.
    
    Args:
        channels: Dictionary mapping channel numbers to values
        
    Returns:
        True if all channels set successfully
        
    Raises:
        DMXError: If any channel or value is invalid
    """
    for ch, val in channels.items():
        set_channel(ch, val)
    return True


def send_blackout() -> None:
    """Send blackout (all channels to 0) to DMX universe."""
    global dmx_universe
    dmx_universe = [0] * DMX_CHANNELS
    print("🔴 Blackout sent to DMX universe")
    send_artnet()


def get_universe() -> List[ChannelValue]:
    """
    Get a copy of the current DMX universe state.
    
    Returns:
        Copy of DMX universe (512 channels)
    """
    return dmx_universe.copy()


def get_channel(ch: int) -> ChannelValue:
    """
    Get the current value of a specific DMX channel.
    
    Args:
        ch: DMX channel number (1-512)
        
    Returns:
        Current channel value
        
    Raises:
        DMXError: If channel is invalid
    """
    try:
        validate_dmx_channel(ch)
        return dmx_universe[ch - 1]
    except ValueError as e:
        raise DMXError(f"Invalid channel: {e}", channel=ch)


def send_artnet(_dmx_universe: Optional[List[ChannelValue]] = None) -> None:
    """
    Send Art-Net packet with current DMX universe data.
    
    Args:
        _dmx_universe: Optional universe data to send (uses current if None)
        
    Raises:
        NetworkError: If Art-Net transmission fails
    """
    global last_artnet_send, last_packet, dmx_universe

    if _dmx_universe is not None:
        dmx_universe = _dmx_universe

    # Rate limiting
    now = perf_counter()
    if now - last_artnet_send < (1.0 / FPS):
        return
    last_artnet_send = now

    # Prepare 512-byte DMX data
    full_data = dmx_universe[:DMX_CHANNELS] + [0] * (DMX_CHANNELS - len(dmx_universe))
    
    # Build Art-Net packet
    packet = bytearray()
    packet.extend(b'Art-Net\x00')                          # ID
    packet.extend((0x00, 0x50))                            # OpCode: ArtDMX
    packet.extend((0x00, 0x0e))                            # Protocol version
    packet.extend((0x00, 0x00))                            # Sequence + Physical
    packet.extend((ARTNET_UNIVERSE & 0xFF, (ARTNET_UNIVERSE >> 8) & 0xFF))  # Universe
    packet.extend((0x02, 0x00))                            # Data length = 512
    packet.extend(bytes(full_data))
    
    last_packet = full_data.copy()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.sendto(packet, (ARTNET_IP, ARTNET_PORT))
        sock.close()
    except Exception as e:
        raise NetworkError(f"Art-Net send error: {e}", host=ARTNET_IP, port=ARTNET_PORT)


def get_artnet_config() -> Dict[str, Any]:
    """
    Get current Art-Net configuration.
    
    Returns:
        Dictionary with Art-Net settings
    """
    return {
        "ip": ARTNET_IP,
        "port": ARTNET_PORT,
        "universe": ARTNET_UNIVERSE,
        "fps": FPS,
        "channels": DMX_CHANNELS
    }


def set_artnet_config(ip: Optional[str] = None, universe: Optional[int] = None) -> None:
    """
    Update Art-Net configuration.
    
    Args:
        ip: Art-Net target IP address
        universe: Art-Net universe number
    """
    global ARTNET_IP, ARTNET_UNIVERSE
    
    if ip is not None:
        ARTNET_IP = ip
    if universe is not None:
        ARTNET_UNIVERSE = universe
