"""
End-to-end test of the heartbeat monitor.

Imports the app module directly (does NOT run Flask), starts the heartbeat
thread, simulates a server dying via the mock's _set_alive helper, then
verifies the dead server is replaced.

Run from loadbalancer/:
    python test_heartbeat.py
"""
import threading
import time

import app
from _mocks.mock_docker import _set_alive


def main():
    # Speed up the heartbeat for testing (default 5s is too slow to watch).
    app.HEARTBEAT_INTERVAL = 0.5

    # Bootstrap the 3 default servers.
    app._bootstrap_initial_servers()
    before = sorted(app.name_to_id.keys())
    print(f"Before:           {before}")
    assert before == ["Server-1", "Server-2", "Server-3"], "bootstrap failed"

    # Start the heartbeat thread.
    t = threading.Thread(target=app._heartbeat_loop, name="heartbeat", daemon=True)
    t.start()

    # Simulate Server-2 dying. The mock will report alive=False.
    print("Killing Server-2 (simulated)...")
    _set_alive("Server-2", False)

    # Give the heartbeat time to notice (at most ~2 cycles).
    time.sleep(2.0)

    after = sorted(app.name_to_id.keys())
    print(f"After:            {after}")

    # Server-2 should be gone; one new server should have appeared.
    assert "Server-2" not in after, "Server-2 was not removed"
    assert len(after) == 3, f"expected 3 servers, found {len(after)}: {after}"
    assert any(n.startswith("S_") for n in after), \
        "expected an auto-generated replacement (S_xxxxxx)"

    print("PASS: dead server was replaced with a fresh one")

    # Clean shutdown of the heartbeat thread.
    app._heartbeat_stop.set()
    t.join(timeout=1.0)


if __name__ == "__main__":
    main()
