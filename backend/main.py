from flask import Flask, jsonify, send_from_directory, request
import os, json

SONGS_DIR = "/app/static/songs"

app = Flask(__name__, static_folder="../static")

# DMX universe (512 channels)
dmx_universe = [0] * 512

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

@app.route("/status")
def status():
    return jsonify({
        "project": "demo_project",
        "playing": True,
        "timecode": "00:01:23.456",
        "next_cue": {"time": "00:01:25.000", "target": "par_1", "action": "fade_rgb", "color": [255, 0, 0]}
    })

@app.route("/songs/save", methods=["POST"])
def save_arrangement():
    data = request.get_json()
    filepath = os.path.join(SONGS_DIR, data["file"])
    try:
        with open(filepath, "w") as f:
            json.dump(data["data"], f, indent=2)
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

@app.route("/dmx/universe", methods=["GET"])
def get_universe():
    return jsonify({"universe": dmx_universe})

@app.route("/dmx/set", methods=["POST"])
def set_dmx_values():
    data = request.get_json()
    if "values" not in data or not isinstance(data["values"], dict):
        return jsonify({"error": "Missing or invalid 'values'"}), 400

    updates = {}
    for channel_str, value in data["values"].items():
        try:
            ch = int(channel_str)
            val = int(value)
            if 0 <= ch < 512 and 0 <= val <= 255:
                dmx_universe[ch] = val
                updates[ch] = val
            else:
                return jsonify({"error": f"Invalid channel or value: {ch}={val}"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 400

    return jsonify({"updated": updates})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
