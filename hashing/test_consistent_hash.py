"""
Unit tests for ConsistentHash. See docs/TEAM.md section 3.

Run from the hashing/ directory:
    pytest -v
"""
import random
from collections import Counter

import pytest

from consistent_hash import ConsistentHash


def test_empty_ring():
    """A fresh ring has no servers."""
    ch = ConsistentHash()
    assert ch.list_servers() == []


def test_add_servers_basic():
    """After adding 1, 2, 3 they're all listed."""
    ch = ConsistentHash(slots=512, virtuals=9)
    for s in (1, 2, 3):
        ch.add_server(s)
    assert sorted(ch.list_servers()) == [1, 2, 3]


def test_get_server_deterministic():
    """Same request id always maps to the same server."""
    ch = ConsistentHash()
    for s in (1, 2, 3):
        ch.add_server(s)
    rid = 132574
    first = ch.get_server(rid)
    for _ in range(100):
        assert ch.get_server(rid) == first


def test_distribution_sanity():
    """10000 random requests on N=3 - no server <20% or >50%."""
    ch = ConsistentHash()
    for s in (1, 2, 3):
        ch.add_server(s)
    random.seed(42)
    counts = Counter(
        ch.get_server(random.randint(0, 999_999)) for _ in range(10000)
    )
    for sid, c in counts.items():
        pct = c / 10000
        assert 0.20 <= pct <= 0.50, f"server {sid} got {pct:.2%}"


def test_add_remove_invariance():
    """Adding then removing server 4 must leave the other mappings unchanged."""
    base = ConsistentHash()
    for s in (1, 2, 3):
        base.add_server(s)
    baseline = {r: base.get_server(r) for r in range(1000)}

    test = ConsistentHash()
    for s in (1, 2, 3, 4):
        test.add_server(s)
    test.remove_server(4)
    after = {r: test.get_server(r) for r in range(1000)}

    assert baseline == after


def test_probing_forced_collision():
    """Small ring forces collisions; all virtuals must still place uniquely."""
    ch = ConsistentHash(slots=8, virtuals=2)
    for s in (1, 2, 3):
        ch.add_server(s)
    assert sorted(ch.list_servers()) == [1, 2, 3]
