import socket

def listen_artnet_packets():
    # Artnet uses UDP and typically listens on port 6454
    ARTNET_PORT = 6454
    BUFFER_SIZE = 1024

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", ARTNET_PORT))

    print(f"Listening for Artnet packets on port {ARTNET_PORT}...")

    while True:
        try:
            # Receive data from the socket
            data, addr = sock.recvfrom(BUFFER_SIZE)

            # Extract and print the DMX channels
            if len(data) < 18:
                print("Received packet too short to contain DMX data.")
                return
            # Check for Art-Net header
            if data[:8] != b'Art-Net\x00':
                print("Received packet does not start with Art-Net header.")
                return
            # Extract the universe and DMX data
            universe = data[14] | (data[15] << 8)
            dmx_data = data[18:18 + 512]  # DMX data
            if len(dmx_data) < 512:
                print("Received packet does not contain full DMX data.")
                return

            # Extract DMX channels
            dmx_channels = [v for v in dmx_data[:512]]  # Convert to list of integers
            print(dmx_log(dmx_channels[:40]))  # Log the received data

        except KeyboardInterrupt:
            print("Stopping Artnet listener.")
            break
        except Exception as e:
            print(f"Error: {e}")



def dmx_log(dmx_universe, time = None, universe=None):
    """
    format the DMX universe data for logging.
    This function formats the DMX universe data into a string for logging.

    """
    ret = ""
    if universe is not None:
        ret += f"u{universe} | "
    if time is not None:
      ret = f"{time:.3f} | "
    ret += '.'.join(f"{v:03d}" for v in dmx_universe)
    ret = ret.replace('000', '   ') # replace empty channels with spaces
    return ret

if __name__ == "__main__":
    listen_artnet_packets()