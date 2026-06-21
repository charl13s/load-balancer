"""
Minimal Flask web server for Task 1.

See docs/TEAM.md section 4 Part 1 (Person C) for specification.
"""
import os
from flask import Flask, jsonify

app = Flask(__name__)

SERVER_ID = os.environ.get("SERVER_ID", "unknown")


@app.route("/home", methods=["GET"])
def home():
    # TODO Person C: return JSON
    #   {"message": "Hello from Server: <ID>", "status": "successful"}
    # with HTTP 200, where <ID> is SERVER_ID.
    raise NotImplementedError("Person C: implement /home")


@app.route("/heartbeat", methods=["GET"])
def heartbeat():
    # TODO Person C: return empty body with HTTP 200.
    # Hint: ("", 200)
    raise NotImplementedError("Person C: implement /heartbeat")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
