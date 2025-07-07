# dmx_state.py

from time import perf_counter
import socket

# --- DMX Constants ---
DMX_CHANNELS = 512
FPS = 60
ARTNET_PORT = 6454
ARTNET_IP = "192.168.1.221" # real 192.168.1.221
ARTNET_UNIVERSE = 0

# --- DMX State ---
dmx_universe = [0] * DMX_CHANNELS
last_artnet_send = 0
last_packet = [0] * DMX_CHANNELS

# --- DMX Controller Functions ---
def set_channel(ch: int, val: int) -> bool:
    if 0 <= ch < DMX_CHANNELS and 0 <= val <= 255:
        dmx_universe[ch-1] = val
        return True
    return False

def get_universe():
    return dmx_universe.copy()

# --- Send ArtNet packet ---
def send_artnet(_dmx_universe=None):
    global last_artnet_send, last_packet, dmx_universe

    if _dmx_universe is not None:
        dmx_universe = _dmx_universe

    now = perf_counter()
    if now - last_artnet_send < (1.0 / FPS):
        return
    last_artnet_send = now

    # Full 512-byte DMX data
    full_data = dmx_universe[:DMX_CHANNELS] + [0] * (DMX_CHANNELS - len(dmx_universe))
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
        print(f"❌ Art-Net send error: {e}")
