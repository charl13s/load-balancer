"""
Consistent hashing data structure for ICS 4104 Assignment 1, Task 2.

See docs/TEAM.md section 3 (Person B) for full specification.
See the assignment PDF (docs/DS_Assign_LB_2024_1.pdf) for the algorithm description.

PARAMETERS (from spec):
    M (slots)    = 512
    K (virtuals) = 9    (= log_2(512))
    H(i)         = i*i + 2*i + 17           (request -> slot)
    Phi(i, j)    = i*i + j*j + 2*j + 25     (server (i, j) -> slot)
    All results taken % M.

Probing strategy: TODO - choose linear or quadratic and document in README.
"""


def H(i: int) -> int:
    """Hash function for mapping request IDs to slots."""
    return i * i + 2 * i + 17


def Phi(i: int, j: int) -> int:
    """Hash function for mapping virtual servers to slots.
    i = server_id, j = virtual replica index (0..K-1)."""
    return i * i + j * j + 2 * j + 25


class ConsistentHash:
    def __init__(self, slots: int = 512, virtuals: int = 9):
        """Initialize empty ring with `slots` positions and `virtuals` virtuals per server.

        TODO Person B: pick your data structure.
        Options:
          - list[Optional[int]] of length M (O(1) slot access, O(M) clockwise scan)
          - dict[slot_index, server_id] (sparse storage)
          - sorted list of (slot, server_id) (O(log M) lookup with bisect)
        Trade-offs differ; document your choice.
        """
        self.slots = slots
        self.virtuals = virtuals
        raise NotImplementedError("Person B: implement __init__")

    def add_server(self, server_id: int) -> None:
        """Place K virtual replicas of `server_id` in the ring.
        For j in 0..virtuals-1, compute Phi(server_id, j) % slots and place there.
        On collision: linear or quadratic probing."""
        raise NotImplementedError("Person B: implement add_server")

    def remove_server(self, server_id: int) -> None:
        """Remove all virtual replicas of `server_id` from the ring.
        No-op if server_id is not present."""
        raise NotImplementedError("Person B: implement remove_server")

    def get_server(self, request_id: int) -> int:
        """Map `request_id` to a server_id via clockwise lookup from H(request_id) % slots.
        Raise IndexError if the ring is empty."""
        raise NotImplementedError("Person B: implement get_server")

    def list_servers(self) -> list[int]:
        """Return list of currently registered server_ids (unique, any order)."""
        raise NotImplementedError("Person B: implement list_servers")
