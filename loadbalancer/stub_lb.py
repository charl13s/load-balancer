"""
STUB load balancer - for Person D's async-client development only.

This is NOT the real load balancer. It exists so the async client and the
plotting code can be developed and tested before the real LB is ready.

Behavior:
  - /home returns the same JSON shape as the real LB
  - SERVER_ID rotates round-robin through {1, 2, 3} per request
  - /rep, /add, /rm return stubbed but spec-shaped responses
  - state is in-memory; restart resets it

Run locally:
    cd loadbalancer
    pip install flask
    python stub_lb.py
    # then in another terminal:
    curl http://localhost:5000/home
    curl http://localhost:5000/rep
"""
import itertools
from flask import Flask, jsonify, request

app = Flask(__name__)
_server_cycle = itertools.cycle([1, 2, 3])
_replicas = ["Server 1", "Server 2", "Server 3"]


@app.route("/home", methods=["GET"])
def home():
    sid = next(_server_cycle)
    return jsonify({
        "message": f"Hello from Server: {sid}",
        "status": "successful",
    }), 200


@app.route("/rep", methods=["GET"])
def rep():
    return jsonify({
        "message": {"N": len(_replicas), "replicas": list(_replicas)},
        "status": "successful",
    }), 200


@app.route("/add", methods=["POST"])
def add():
    data = request.get_json(force=True, silent=True) or {}
    n = int(data.get("n", 0))
    hosts = list(data.get("hostnames", []))
    if len(hosts) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure",
        }), 400
    for h in hosts:
        if h not in _replicas:
            _replicas.append(h)
    auto_needed = n - len(hosts)
    for _ in range(auto_needed):
        _replicas.append(f"S_auto_{len(_replicas) + 1}")
    return jsonify({
        "message": {"N": len(_replicas), "replicas": list(_replicas)},
        "status": "successful",
    }), 200


@app.route("/rm", methods=["DELETE"])
def rm():
    data = request.get_json(force=True, silent=True) or {}
    n = int(data.get("n", 0))
    hosts = list(data.get("hostnames", []))
    if len(hosts) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure",
        }), 400
    for h in hosts:
        if h in _replicas:
            _replicas.remove(h)
    remaining = n - len(hosts)
    while remaining > 0 and _replicas:
        _replicas.pop()
        remaining -= 1
    return jsonify({
        "message": {"N": len(_replicas), "replicas": list(_replicas)},
        "status": "successful",
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
