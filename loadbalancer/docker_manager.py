"""
Docker container management module for the load balancer.

See docs/TEAM.md section 4 Part 2 (Person C) for specification.

Implementation suggestion: use the official `docker` Python SDK
(`pip install docker`). Cleaner than os.popen("docker run ...").

Quick reference:
    import docker
    client = docker.from_env()
    client.containers.run("image:tag", name=..., network=..., detach=True, ...)
    client.containers.get(name).stop()
    client.containers.list(filters={"label": "lb-managed=true"})
"""
from typing import List


def spawn_server(
    name: str,
    server_id: int,
    network: str = "net1",
    image: str = "lb-server:latest",
) -> bool:
    """Start a new container named `name`.

    Requirements:
      - container name = `name`
      - connected to `network` with network_alias = `name`
      - env var SERVER_ID = server_id
      - label "lb-managed=true" so list_servers can filter
      - detached (-d)

    Returns True on success, False otherwise.
    Catch docker.errors.APIError and return False rather than raising.
    """
    raise NotImplementedError("Person C: implement spawn_server")


def kill_server(name: str) -> bool:
    """Stop and remove container `name`. Return True on success, False otherwise.

    Should be idempotent: removing an already-removed container is not an error.
    """
    raise NotImplementedError("Person C: implement kill_server")


def list_servers(network: str = "net1") -> List[str]:
    """Return names of all running lb-managed containers on `network`.

    Filter by label "lb-managed=true" so unrelated containers on the host
    don't show up.
    """
    raise NotImplementedError("Person C: implement list_servers")


def is_alive(name: str, timeout: float = 2.0) -> bool:
    """GET http://<name>:5000/heartbeat. Return True iff status code is 200.

    NOTE: This only works when called from inside a container on `net1`,
    because the hostname `name` resolves via Docker's internal DNS.
    Charles will exercise this during integration.

    Use `requests.get(..., timeout=timeout)`. Return False on any exception.
    """
    raise NotImplementedError("Person C: implement is_alive")
