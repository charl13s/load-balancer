"""
Docker container management module for the load balancer.

Uses the docker Python SDK (`pip install docker>=7.0`) to manage server
containers via the host's /var/run/docker.sock. The LB process must have
the socket mounted (handled in docker-compose.yml).

All functions are idempotent where it makes sense:
  - spawn_server cleans up any stale container with the same name first
  - kill_server treats "already gone" as success
  - list_servers filters by lb-managed label so unrelated containers don't
    appear in our view of the world
"""
import logging
from typing import List

import docker
import requests
from docker.errors import APIError, NotFound

logger = logging.getLogger(__name__)

# Lazy-initialized client - we don't connect to the daemon at import time so
# tests can patch this if needed and the module imports cleanly even when
# the daemon isn't running.
_client = None


def _get_client():
    """Return a singleton docker client connected to /var/run/docker.sock."""
    global _client
    if _client is None:
        _client = docker.from_env()
    return _client


# Label used to tag containers we manage. Lets list_servers() filter out
# unrelated containers running on the host.
LABEL_KEY = "lb-managed"
LABEL_VALUE = "true"


def spawn_server(
    name: str,
    server_id: int,
    network: str = "net1",
    image: str = "lb-server:latest",
) -> bool:
    """Start a new container named `name` on `network` with SERVER_ID=server_id.

    Args:
        name: Container name and DNS-resolvable hostname on `network`.
        server_id: Integer passed as env var SERVER_ID to the container.
        network: Docker network to attach to (must already exist).
        image: Image to run. Defaults to the server image from Task 1.

    Returns:
        True on success, False on any docker API error.
    """
    try:
        client = _get_client()

        # Defensive: if a stale container with this name exists (e.g. left
        # over from a crash), remove it before spawning.
        try:
            existing = client.containers.get(name)
            existing.remove(force=True)
            logger.info("removed stale container %s before spawning", name)
        except NotFound:
            pass

        client.containers.run(
            image=image,
            name=name,
            detach=True,
            network=network,
            environment={"SERVER_ID": str(server_id)},
            labels={LABEL_KEY: LABEL_VALUE},
        )
        logger.info("spawned %s (server_id=%s, image=%s)", name, server_id, image)
        return True
    except APIError as e:
        logger.error("spawn_server(%s) docker API error: %s", name, e)
        return False
    except Exception as e:  # noqa: BLE001 - log and fail rather than crash the LB
        logger.exception("spawn_server(%s) unexpected error", name)
        return False


def kill_server(name: str) -> bool:
    """Stop and remove container `name`.

    Idempotent: returns True even if the container is already gone, because
    'goal achieved' is the same regardless of how it was achieved.
    """
    try:
        client = _get_client()
        try:
            container = client.containers.get(name)
        except NotFound:
            return True  # already gone
        container.remove(force=True)  # force=True stops the container if running
        logger.info("killed %s", name)
        return True
    except APIError as e:
        logger.error("kill_server(%s) docker API error: %s", name, e)
        return False


def list_servers(network: str = "net1") -> List[str]:
    """Return names of all running lb-managed containers attached to `network`.

    Filters by the lb-managed label so unrelated containers on the host don't
    leak into our view.
    """
    try:
        client = _get_client()
        containers = client.containers.list(
            filters={"label": f"{LABEL_KEY}={LABEL_VALUE}"},
        )
        result = []
        for c in containers:
            networks = c.attrs.get("NetworkSettings", {}).get("Networks", {})
            if network in networks:
                result.append(c.name)
        return result
    except APIError as e:
        logger.error("list_servers docker API error: %s", e)
        return []


def is_alive(name: str, timeout: float = 2.0) -> bool:
    """Check if the Flask server inside container `name` is responsive.

    Makes a GET to http://<name>:5000/heartbeat and returns True iff HTTP 200.

    IMPORTANT: this only works when called from inside a container attached
    to the same Docker network as <name>, because the hostname resolves via
    Docker's internal DNS. From the host, the lookup will fail.
    """
    try:
        r = requests.get(f"http://{name}:5000/heartbeat", timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False
    except Exception:  # noqa: BLE001
        return False
