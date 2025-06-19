import socket
import struct

ARTNET_PORT = 6454
ARTNET_HEADER = b'Art-Net\x00'
OP_DMX = 0x5000  # Opcode for ArtDMX (little-endian)

last_dmx_data = [0] * 512  # Store last received DMX state

def parse_artdmx_packet(data):
    if not data.startswith(ARTNET_HEADER):
        return None

    opcode = struct.unpack('<H', data[8:10])[0]
    if opcode != OP_DMX:
        return None

    sequence = data[12]
    physical = data[13]
    universe = struct.unpack('<H', data[14:16])[0]
    length = struct.unpack('>H', data[16:18])[0]  # Big-endian
    dmx_data = data[18:18+length]

    return {
        'sequence': sequence,
        'physical': physical,
        'universe': universe,
        'length': length,
        'dmx_data': dmx_data
    }

def format_nonzero_channels(dmx_data):
    return ' | '.join(
        f"{i+1}: {val}"
        for i, val in enumerate(dmx_data)
        if val > 0
    )

def format_changed_channels(dmx_data, last_data):
    return ' | '.join(
        f"{i+1}: {val}"
        for i, (val, last_val) in enumerate(zip(dmx_data, last_data))
        if val != last_val
    )

def start_listener():
    global last_dmx_data

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', ARTNET_PORT))
    print(f"Listening for Art-Net packets on UDP port {ARTNET_PORT}...\n")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            result = parse_artdmx_packet(data)
            if result:
                print(f"[From {addr[0]}]")
                print(f"Universe: {result['universe']}, Seq: {result['sequence']}, Length: {result['length']}")
                print("Raw DMX Data (first 32 channels):", list(result['dmx_data'][:32]))

                formatted_all = format_nonzero_channels(result['dmx_data'])
                print("All Non-zero Values:", formatted_all if formatted_all else "(All values are 0)")

                formatted_changes = format_changed_channels(result['dmx_data'], last_dmx_data)
                print("Changed Values:", formatted_changes if formatted_changes else "(No changes)")

                last_dmx_data[:result['length']] = result['dmx_data']  # Update only received length
                print('-' * 60)
    except KeyboardInterrupt:
        print("\nExiting listener.")

if __name__ == "__main__":
    start_listener()
