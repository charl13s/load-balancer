"""
Manual end-to-end test of docker_manager.

Prerequisites:
    1. lb-server:latest image built from server/  (docker build -t lb-server:latest .)
    2. net1 network created                       (docker network create net1)

Run from loadbalancer/:
    python test_docker_manager.py

If you Ctrl+C mid-run, clean up leftover containers with:
    docker ps -a --filter label=lb-managed=true --format '{{.Names}}' | xargs -r docker rm -f
"""
import time

import docker_manager as dm


def main() -> None:
    # Start from a clean slate.
    for existing in dm.list_servers():
        dm.kill_server(existing)
    assert dm.list_servers() == [], "could not clean pre-existing lb-managed containers"

    # 1. spawn two test containers
    assert dm.spawn_server("dm-test-s1", 1), "spawn dm-test-s1 failed"
    assert dm.spawn_server("dm-test-s2", 2), "spawn dm-test-s2 failed"
    print("spawn_server: OK")

    # Give containers a moment to register with Docker before listing.
    time.sleep(0.5)

    # 2. list_servers shows both, only them
    running = sorted(dm.list_servers())
    assert running == ["dm-test-s1", "dm-test-s2"], f"unexpected list: {running}"
    print("list_servers: OK ->", running)

    # 3. NOTE: is_alive is NOT testable from the host. The hostname dm-test-s1
    # resolves only via Docker DNS, which is only available to containers on
    # the same network. Charles exercises is_alive during LB integration.

    # 4. kill one container, list should drop it
    assert dm.kill_server("dm-test-s1"), "kill_server(dm-test-s1) failed"
    remaining = sorted(dm.list_servers())
    assert remaining == ["dm-test-s2"], f"after kill: {remaining}"
    print("kill_server: OK")

    # 5. idempotent kill of nonexistent container should succeed
    assert dm.kill_server("dm-test-nonexistent"), "idempotent kill should be True"
    print("idempotent kill: OK")

    # 6. cleanup
    dm.kill_server("dm-test-s2")
    assert dm.list_servers() == [], "final cleanup failed"

    print("\nALL TESTS PASSED")


if __name__ == "__main__":
    main()
