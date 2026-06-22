"""
Mock docker_manager for LB development before Person C's PR lands.

In-memory state, no real Docker calls. Same interface as the real one.
TODO: DELETE this file once loadbalancer/docker_manager.py has the real impl.
"""
import threading

_lock = threading.Lock()
_containers: dict[str, dict] = {}   # name -> {"server_id": int, "alive": bool}


def spawn_server(name: str, server_id: int, network: str = "net1",
                 image: str = "lb-server:latest") -> bool:
    with _lock:
        if name in _containers:
            return False
        _containers[name] = {"server_id": server_id, "alive": True}
        return True


def kill_server(name: str) -> bool:
    with _lock:
        if name in _containers:
            del _containers[name]
            return True
        return False


def list_servers(network: str = "net1") -> list[str]:
    with _lock:
        return list(_containers.keys())


def is_alive(name: str, timeout: float = 2.0) -> bool:
    with _lock:
        return _containers.get(name, {}).get("alive", False)


# --- test helper, NOT part of the real interface ---
def _set_alive(name: str, alive: bool) -> None:
    """Simulate a server going up/down. Only exists in the mock."""
    with _lock:
        if name in _containers:
            _containers[name]["alive"] = alive
