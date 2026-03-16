from flask import Flask, render_template, request, jsonify
from walle.serial import WalleSerial
from walle.config import WalleConfig
from walle_brain import WalleBrain
import threading

app = Flask(__name__)

_robot = None
_lock  = threading.Lock()
_stepper_thread = None
_brain = WalleBrain()

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


# --- LED ---

@app.route("/led", methods=["POST"])
def led():
    data = request.get_json()
    r = int(data.get("r", 0))
    g = int(data.get("g", 0))
    b = int(data.get("b", 0))
    with _lock:
        get_robot().led(r, g, b)
    return jsonify(ok=True)


@app.route("/calibration", methods=["GET"])
def get_calibration():
    return jsonify(_calibration)


@app.route("/calibration", methods=["POST"])
def set_calibration():
    data = request.get_json()
    for ch in ("r", "g", "b"):
        if ch in data:
            _calibration[ch] = max(0.0, min(1.0, float(data[ch])))
    WalleConfig.R_SCALE = _calibration["r"]
    WalleConfig.G_SCALE = _calibration["g"]
    WalleConfig.B_SCALE = _calibration["b"]
    return jsonify(ok=True, **_calibration)


# --- SERVO ---

@app.route("/servo", methods=["POST"])
def servo():
    data = request.get_json()
    angle = int(max(0, min(180, data.get("angle", 90))))
    with _lock:
        get_robot().servo(angle)
    return jsonify(ok=True, angle=angle)


# --- STEPPER ---

@app.route("/stepper", methods=["POST"])
def stepper():
    global _stepper_thread
    data = request.get_json()
    steps = int(data.get("steps", 512))

    # Stepper est bloquant — on le lance dans un thread pour ne pas bloquer Flask
    if _stepper_thread and _stepper_thread.is_alive():
        return jsonify(ok=False, error="Stepper already running"), 409

    def run():
        with _lock:
            get_robot().stepper(steps)

    _stepper_thread = threading.Thread(target=run, daemon=True)
    _stepper_thread.start()
    return jsonify(ok=True, steps=steps)


@app.route("/stepper/status")
def stepper_status():
    busy = _stepper_thread is not None and _stepper_thread.is_alive()
    return jsonify(busy=busy)


# --- CHAT ---

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify(ok=False, error="empty message"), 400

    reply = _brain.think(message)
    return jsonify(ok=True, reply=reply)


@app.route("/chat/reset", methods=["POST"])
def chat_reset():
    _brain.reset()
    return jsonify(ok=True)


def main():
    app.run(host="0.0.0.0", port=5000, debug=False)
