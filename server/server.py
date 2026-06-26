"""
Minimal Flask web server for Task 1.

Endpoints (both port 5000):
    GET /home       JSON {"message": "Hello from Server: <ID>", "status": "successful"}
    GET /heartbeat  empty body, HTTP 200 (used by LB to detect failures)

SERVER_ID is read from the environment variable so a single image can run
as multiple distinct containers via `docker run -e SERVER_ID=N ...`.
"""
import os

from flask import Flask, jsonify

app = Flask(__name__)

SERVER_ID = os.environ.get("SERVER_ID", "unknown")


@app.route("/home", methods=["GET"])
def home():
    return jsonify({
        "message": f"Hello from Server: {SERVER_ID}",
        "status": "successful",
    }), 200


@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    # Empty body with HTTP 200, per spec.
    return ("", 200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
