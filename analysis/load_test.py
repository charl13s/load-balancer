"""
Async load tester for Task 4.

See docs/TEAM.md section 5 (Person D) for spec and experiments.

This skeleton IS runnable against the stub LB. Person D fills in the
experiment-specific orchestration.

Quick sanity test:
    # terminal 1
    cd ../loadbalancer && python stub_lb.py

    # terminal 2
    cd analysis
    pip install -r requirements.txt
    python load_test.py --n-requests 1000 --url http://localhost:5000/home --out results/sanity.csv
"""
import argparse
import asyncio
import csv
import re
import time
from pathlib import Path

import aiohttp

SERVER_ID_RE = re.compile(r"Hello from Server:\s*(\S+)")


async def one_request(session, url, req_id):
    """Fire one GET. Returns tuple (request_id, server_id, latency_ms, ok)."""
    t0 = time.perf_counter()
    try:
        async with session.get(url) as r:
            body = await r.json()
            latency_ms = (time.perf_counter() - t0) * 1000
            msg = body.get("message", "")
            m = SERVER_ID_RE.search(msg) if isinstance(msg, str) else None
            sid = m.group(1) if m else "unknown"
            return (req_id, sid, latency_ms, r.status == 200)
    except Exception:
        latency_ms = (time.perf_counter() - t0) * 1000
        return (req_id, "error", latency_ms, False)


async def run(url: str, n: int, concurrency: int, out_path: Path):
    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [one_request(session, url, i) for i in range(n)]
        results = await asyncio.gather(*tasks)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["request_id", "server_id", "latency_ms", "ok"])
        w.writerows(results)
    ok = sum(1 for r in results if r[3])
    print(f"Wrote {len(results)} rows to {out_path}  ({ok} ok, {len(results)-ok} failed)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:5000/home")
    p.add_argument("--n-requests", type=int, default=10000)
    p.add_argument("--concurrency", type=int, default=200)
    p.add_argument("--out", default="results/raw_data.csv")
    args = p.parse_args()
    asyncio.run(run(args.url, args.n_requests, args.concurrency, Path(args.out)))


if __name__ == "__main__":
    main()
