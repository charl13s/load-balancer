"""
Mock ConsistentHash for LB development before Person B's PR lands.

Same interface as the real one, simplified logic (round-robin/modulo).
TODO: DELETE this file once loadbalancer/consistent_hash.py has the real impl.
"""
import threading


class MockConsistentHash:
    def __init__(self, slots: int = 512, virtuals: int = 9):
        self.slots = slots
        self.virtuals = virtuals
        self._servers: list[int] = []   # ordered list of server_ids
        self._lock = threading.Lock()

    def add_server(self, server_id: int) -> None:
        with self._lock:
            if server_id not in self._servers:
                self._servers.append(server_id)

    def remove_server(self, server_id: int) -> None:
        with self._lock:
            if server_id in self._servers:
                self._servers.remove(server_id)

    def get_server(self, request_id: int) -> int:
        with self._lock:
            if not self._servers:
                raise IndexError("ring is empty")
            # NOT real consistent hashing - just deterministic modulo
            # so we can test the LB end-to-end. Person B's impl replaces this.
            return self._servers[request_id % len(self._servers)]

    def list_servers(self) -> list[int]:
        with self._lock:
            return list(self._servers)
