from flask import Flask, render_template, request, jsonify
from walle.serial import WalleSerial
from walle.config import WalleConfig
import threading

app = Flask(__name__)

_robot = None
_lock  = threading.Lock()

def get_robot():
    global _robot
    if _robot is None:
        _robot = WalleSerial()
    return _robot


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/led", methods=["POST"])
def led():
    data = request.get_json()
    r = int(data.get("r", 0))
    g = int(data.get("g", 0))
    b = int(data.get("b", 0))
    with _lock:
        get_robot().led(r, g, b)
    return jsonify(ok=True, r=r, g=g, b=b)


def main():
    app.run(host="0.0.0.0", port=5000, debug=False)
