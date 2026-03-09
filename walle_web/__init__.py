from flask import Flask, render_template, request, jsonify
from walle.serial import WalleSerial
from walle.config import WalleConfig
import threading

app = Flask(__name__)

_robot = None
_lock  = threading.Lock()

# Calibration en mémoire (modifiable depuis l'interface)
_calibration = {
    "r": WalleConfig.R_SCALE,
    "g": WalleConfig.G_SCALE,
    "b": WalleConfig.B_SCALE,
}

def get_robot():
    global _robot
    if _robot is None:
        _robot = WalleSerial()
    return _robot


@app.route("/")
def index():
    return render_template("index.html", cal=_calibration)


@app.route("/led", methods=["POST"])
def led():
    data = request.get_json()
    r = int(data.get("r", 0))
    g = int(data.get("g", 0))
    b = int(data.get("b", 0))
    with _lock:
        get_robot().led(r, g, b)
    return jsonify(ok=True, r=r, g=g, b=b)


@app.route("/calibration", methods=["GET"])
def get_calibration():
    return jsonify(_calibration)


@app.route("/calibration", methods=["POST"])
def set_calibration():
    data = request.get_json()
    for ch in ("r", "g", "b"):
        if ch in data:
            val = max(0.0, min(1.0, float(data[ch])))
            _calibration[ch] = val
    # Applique immédiatement en mettant à jour le robot
    with _lock:
        robot = get_robot()
        robot._config_r = _calibration["r"]
        robot._config_g = _calibration["g"]
        robot._config_b = _calibration["b"]
        WalleConfig.R_SCALE = _calibration["r"]
        WalleConfig.G_SCALE = _calibration["g"]
        WalleConfig.B_SCALE = _calibration["b"]
    return jsonify(ok=True, **_calibration)


def main():
    app.run(host="0.0.0.0", port=5000, debug=False)
