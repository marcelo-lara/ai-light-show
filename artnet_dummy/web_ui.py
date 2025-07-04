from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading
import socket

app = Flask(__name__)

# Initialize SocketIO
socketio = SocketIO(app)

# Shared DMX data
current_dmx_data = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dmx_data')
def dmx_data():
    return jsonify(current_dmx_data)

@socketio.on('connect')
def handle_connect():
    print("Client connected")
    emit('dmx_update', current_dmx_data)  # Send initial data on connection

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('dmx_update')
def handle_dmx_update():
    print("dmx_update event emitted")

# Debugging logs for emitted data
print("Emitting DMX data:", current_dmx_data[:40])

def listen_artnet_packets():
    ARTNET_PORT = 6454
    BUFFER_SIZE = 1024

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", ARTNET_PORT))

    print(f"Listening for Artnet packets on port {ARTNET_PORT}...")

    global current_dmx_data

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)

            if len(data) < 18 or data[:8] != b'Art-Net\x00':
                continue

            dmx_data = data[18:18 + 512]
            current_dmx_data = [v for v in dmx_data[:512]]

            # Emit DMX data to all connected clients
            socketio.emit('dmx_update', current_dmx_data)
            print(f"Received DMX data from {addr}: {current_dmx_data[:40]}")  # Log first 40 channels
            print(f"Emitted DMX data: {current_dmx_data[:40]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    threading.Thread(target=listen_artnet_packets, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5501)
