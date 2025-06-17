from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server

def log_osc(addr, *args):
    print(f"{addr} -> {args}")

dispatcher = Dispatcher()
dispatcher.map("/live/status", log_osc)
dispatcher.map("/live/time", log_osc)
dispatcher.map("/live/project", log_osc)

server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 9000), dispatcher)
print("🎧 Listening for OSC from Ableton Live...")
server.serve_forever()