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

def send_blackout():
    global dmx_universe
    dmx_universe = [0] * DMX_CHANNELS
    print("🔴 Blackout sent to DMX universe")
    blackout_frame = bytes([0] * 512)
    send_artnet(0, blackout_frame)

def get_universe():
    return dmx_universe.copy()

# --- Send ArtNet packet ---
def send_artnet(universe: int, frame: bytes):
    global last_artnet_send, last_packet

    # Use frame directly without modifying global state
    now = perf_counter()

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

from .services.dmx.dmx_canvas import DmxCanvas
import time

from threading import Lock, Event

class DMXPlaybackController:
    def __init__(self):
        self._lock = Lock()
        self._stop_event = Event()
        self._is_sending = False
        self._current_canvas = None

    def start_playback(self, canvas: DmxCanvas):
        with self._lock:
            if self._is_sending:
                return
            self._is_sending = True
            self._current_canvas = canvas
            self._stop_event.clear()
            
            import threading
            threading.Thread(target=self._playback_loop, daemon=True).start()

    def stop_playback(self):
        with self._lock:
            self._is_sending = False
            self._stop_event.set()

    def _playback_loop(self):
        with self._lock:
            if not self._current_canvas:
                return
            
            fps = self._current_canvas.fps
            frame_duration = 1.0 / fps
            start_time = time.perf_counter()
            next_frame_time = start_time

        while not self._stop_event.is_set():
            with self._lock:
                if not self._is_sending or not self._current_canvas:
                    break
                
                # Calculate exact frame number based on elapsed time
                elapsed = time.perf_counter() - start_time
                frame_number = int(elapsed * fps)
                frame_time = frame_number / fps
                frame = self._current_canvas.get_frame(frame_time)
                
                # Only send if we've advanced to the next frame
                if time.perf_counter() >= next_frame_time:
                    # Log channels 20-40 (1-based DMX channels, 0-based list index 19-39)
                    print(f"📡 Sending frame {frame_number} @ {frame_time:.3f}s - Ch20-40: {list(frame[19:40])}")
                    send_artnet(0, bytes(frame))
                    next_frame_time += frame_duration
            
            # Sleep precisely until next frame or stop signal
            sleep_time = max(0, next_frame_time - time.perf_counter())
            self._stop_event.wait(sleep_time)

# Singleton playback controller
playback_controller = DMXPlaybackController()

def send_canvas_frames(canvas: DmxCanvas):
    """Start DMX playback with thread-safety guarantees"""
    playback_controller.start_playback(canvas)

def stop_playback():
    """Stop ongoing DMX playback"""
    playback_controller.stop_playback()
