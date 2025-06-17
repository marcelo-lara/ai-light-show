from flask import  Flask, jsonify, send_from_directory, request
import os, json

SONGS_DIR = "/app/static/songs"

app = Flask(__name__, static_folder="../static")

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)