"""
Load balancer Flask app for ICS 4104 Assignment 1, Task 3.

SUBSTEP 3a: routes wired with MOCK hashing and MOCK docker_manager.
- Real ConsistentHash from Person B lands in substep 3b (one import change).
- Real docker_manager from Person C lands in substep 3c (one import change).
- Real HTTP proxying of /<path> also lands in 3c.

Note on hostnames:
    The spec PDF uses examples like "Server 1" (with a space). Docker container
    names cannot contain spaces. We use "Server-1" instead. This is documented
    in the final README under Assumptions.
"""
import os
import random
import string
import threading

from flask import Flask, jsonify, request

# === MOCK imports - replace in substeps 3b and 3c =========================
from _mocks.mock_hash import MockConsistentHash as ConsistentHash
from _mocks.mock_docker import (
    spawn_server, kill_server, list_servers, is_alive,
)
# ==========================================================================


app = Flask(__name__)

# --- Configuration (overridable via env vars) ---
DEFAULT_N = int(os.environ.get("DEFAULT_N", "3"))
SLOTS = int(os.environ.get("SLOTS", "512"))
VIRTUALS = int(os.environ.get("VIRTUALS", "9"))

# --- State protected by state_lock ---
ring = ConsistentHash(slots=SLOTS, virtuals=VIRTUALS)
state_lock = threading.Lock()
name_to_id: dict[str, int] = {}      # hostname -> server_id (bridge to the ring)
_next_server_id: int = 1             # monotonic counter; only allocate, never reuse


def _allocate_server_id() -> int:
    """Hand out a fresh server_id. Caller must hold state_lock."""
    global _next_server_id
    sid = _next_server_id
    _next_server_id += 1
    return sid


def _random_hostname() -> str:
    """Generate a random hostname like 'S_a3f7k1'. Used when /add doesn't
    specify enough hostnames for the requested n."""
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"S_{suffix}"


def _bootstrap_initial_servers() -> None:
    """Spawn DEFAULT_N servers at startup so the system is immediately useful.
    Idempotent only when state is empty (called once at process start)."""
    with state_lock:
        for i in range(1, DEFAULT_N + 1):
            name = f"Server-{i}"
            sid = _allocate_server_id()
            if spawn_server(name, sid):
                name_to_id[name] = sid
                ring.add_server(sid)


# =============================================================================
# Routes
# =============================================================================

@app.route("/rep", methods=["GET"])
def rep():
    """Return current replica count and hostnames."""
    with state_lock:
        replicas = list(name_to_id.keys())
    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful",
    }), 200


@app.route("/add", methods=["POST"])
def add():
    """Add `n` new server replicas. `hostnames` is a list of preferred names
    (must be <= n in length). Auto-generate names for the remainder."""
    data = request.get_json(force=True, silent=True) or {}
    n = int(data.get("n", 0))
    hostnames = list(data.get("hostnames", []))

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than newly added instances",
            "status": "failure",
        }), 400

    with state_lock:
        # Resolve which names to actually create: requested ones (skip dupes),
        # then auto-fill to reach n.
        new_names: list[str] = []
        for h in hostnames:
            if h not in name_to_id and h not in new_names:
                new_names.append(h)
        while len(new_names) < n:
            candidate = _random_hostname()
            if candidate not in name_to_id and candidate not in new_names:
                new_names.append(candidate)

        for name in new_names:
            sid = _allocate_server_id()
            if spawn_server(name, sid):
                name_to_id[name] = sid
                ring.add_server(sid)
            # If spawn fails we silently skip; real impl will log.

        replicas = list(name_to_id.keys())

    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful",
    }), 200


@app.route("/rm", methods=["DELETE"])
def rm():
    """Remove `n` replicas. Preferred hostnames are removed first;
    additional removals are picked randomly from the rest."""
    data = request.get_json(force=True, silent=True) or {}
    n = int(data.get("n", 0))
    hostnames = list(data.get("hostnames", []))

    if len(hostnames) > n:
        return jsonify({
            "message": "<Error> Length of hostname list is more than removable instances",
            "status": "failure",
        }), 400

    with state_lock:
        # Requested removals that actually exist
        to_remove = [h for h in hostnames if h in name_to_id]
        # Then fill the remaining slots randomly from what's left
        candidates = [h for h in name_to_id if h not in to_remove]
        random.shuffle(candidates)
        extras_needed = n - len(to_remove)
        if extras_needed > 0:
            to_remove.extend(candidates[:extras_needed])

        for name in to_remove:
            sid = name_to_id.pop(name, None)
            if sid is not None:
                ring.remove_server(sid)
            kill_server(name)

        replicas = list(name_to_id.keys())

    return jsonify({
        "message": {"N": len(replicas), "replicas": replicas},
        "status": "successful",
    }), 200


@app.route("/<path:p>", methods=["GET"])
def proxy(p):
    """Route a client request to one of the server replicas via consistent
    hashing. Only /home is a valid path on our servers (per Task 1 spec)."""
    if p != "home":
        return jsonify({
            "message": f"<Error> '/{p}' endpoint does not exist in server replicas",
            "status": "failure",
        }), 400

    # PDF: assume request IDs are 6-digit random numbers
    request_id = random.randint(100_000, 999_999)

    with state_lock:
        try:
            sid = ring.get_server(request_id)
        except IndexError:
            return jsonify({
                "message": "<Error> No servers available",
                "status": "failure",
            }), 503

    # MOCKED proxy: synthesize what the real server would return.
    # Real HTTP proxy goes here in substep 3c.
    return jsonify({
        "message": f"Hello from Server: {sid}",
        "status": "successful",
    }), 200


if __name__ == "__main__":
    _bootstrap_initial_servers()
    # threaded=True so multiple requests can be served concurrently
    # (we test this in 3a-3 with the async client).
    app.run(host="0.0.0.0", port=5000, threaded=True)
