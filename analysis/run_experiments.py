"""
Experiment orchestration for Task 4 (Person D).

Runs the required experiments against the load balancer, collecting CSV
results and generating charts.

Experiments
-----------
A-1 : Fixed N=3, send 10 000 async requests -> bar chart of per-server counts.
A-2 : Vary N from 2 to 6, send 10 000 requests each -> line chart of avg load
      per server, plus per-N bar charts.
A-3 : Test server failure/recovery. (Requires real Docker manager).
A-4 : Modify hash functions (done by Person B) and re-run A-1 and A-2 to 
      compare distribution.

Usage
-----
    # Terminal 1 — start the stub LB
    cd ../loadbalancer && python stub_lb.py

    # Terminal 2 — run experiments
    cd analysis
    pip install -r requirements.txt
    python run_experiments.py                          # run all experiments
    python run_experiments.py --experiment a1          # just A-1
    python run_experiments.py --experiment a2          # just A-2
    python run_experiments.py --n-requests 5000        # fewer requests (faster)
    python run_experiments.py --lb-url http://host:80  # custom LB address

Notes
-----
- Results (CSVs + PNGs) are saved to analysis/results/ by default.
- When running against stub_lb.py, the distribution will be perfectly even
  (round-robin). The *real* distribution comes from the actual LB with
  consistent hashing — just re-run the same script once it's ready.
- The script calls /rep, /add, /rm on the LB to set the desired N before
  each sub-experiment.
"""
import argparse
import asyncio
import json
import sys
import time
from collections import Counter
from pathlib import Path

# We use urllib so we don't add a new dependency beyond what's already in
# analysis/requirements.txt.  Sync calls to /rep, /add, /rm are fine.
import urllib.request
import urllib.error

from load_test import run as run_load_test
from plots import bar_chart, line_chart, load_csv


# ---------------------------------------------------------------------------
# LB management helpers
# ---------------------------------------------------------------------------

def _json_request(url: str, method: str = "GET", data: dict | None = None) -> dict:
    """Tiny wrapper around urllib for JSON API calls to the LB."""
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url, data=body, method=method,
        headers={"Content-Type": "application/json"} if body else {},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def get_replicas(lb_url: str) -> dict:
    """GET /rep — returns the full JSON response."""
    return _json_request(f"{lb_url}/rep")


def set_server_count(lb_url: str, target_n: int) -> None:
    """Add or remove servers so the LB has exactly *target_n* replicas."""
    rep = get_replicas(lb_url)
    current_n = rep["message"]["N"]
    current_replicas = rep["message"]["replicas"]

    if current_n < target_n:
        diff = target_n - current_n
        _json_request(f"{lb_url}/add", method="POST",
                      data={"n": diff, "hostnames": []})
        print(f"  + Added {diff} server(s)  ({current_n} -> {target_n})")
    elif current_n > target_n:
        diff = current_n - target_n
        to_remove = current_replicas[:diff]
        _json_request(f"{lb_url}/rm", method="DELETE",
                      data={"n": diff, "hostnames": to_remove})
        print(f"  - Removed {diff} server(s)  ({current_n} -> {target_n})")
    else:
        print(f"  OK Already at N={target_n}")

    # Verify
    rep = get_replicas(lb_url)
    actual = rep["message"]["N"]
    names = rep["message"]["replicas"]
    print(f"  Verified: N={actual}, replicas={names}")


# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------

def experiment_a1(lb_url: str, n_requests: int, concurrency: int,
                  results_dir: Path) -> None:
    """A-1: Fixed N=3, send requests, produce a bar chart."""
    print("\n" + "=" * 60)
    print("  EXPERIMENT A-1: Request distribution with N = 3")
    print("=" * 60)

    set_server_count(lb_url, 3)

    csv_path = results_dir / "a1_n3.csv"
    print(f"\n  Sending {n_requests:,} requests to {lb_url}/home ...")
    asyncio.run(run_load_test(
        url=f"{lb_url}/home", n=n_requests,
        concurrency=concurrency, out_path=csv_path,
    ))

    rows = load_csv(csv_path)
    bar_chart(
        rows,
        title=f"A-1: Request Distribution (N=3, {n_requests:,} requests)",
        out=results_dir / "a1_bar_chart.png",
    )
    _print_distribution_summary(rows)


def experiment_a2(lb_url: str, n_requests: int, concurrency: int,
                  results_dir: Path) -> None:
    """A-2: Vary N from 2 to 6, produce bar charts + a line chart."""
    print("\n" + "=" * 60)
    print("  EXPERIMENT A-2: Average load vs N  (N = 2 .. 6)")
    print("=" * 60)

    points: list[tuple[int, float]] = []   # (N, avg_load)

    for n in range(2, 7):
        print(f"\n--- N = {n} {'-' * 45}")
        set_server_count(lb_url, n)
        time.sleep(0.3)  # brief pause for stability

        csv_path = results_dir / f"a2_n{n}.csv"
        print(f"  Sending {n_requests:,} requests ...")
        asyncio.run(run_load_test(
            url=f"{lb_url}/home", n=n_requests,
            concurrency=concurrency, out_path=csv_path,
        ))

        rows = load_csv(csv_path)
        ok_rows = [r for r in rows if r["ok"] == "True"]
        counts = Counter(r["server_id"] for r in ok_rows)
        avg_load = len(ok_rows) / n if n else 0
        points.append((n, avg_load))

        print(f"  OK={len(ok_rows):,}  unique servers={len(counts)}"
              f"  avg load/server={avg_load:.1f}")

        # Per-N bar chart
        bar_chart(
            rows,
            title=f"A-2: Distribution (N={n}, {n_requests:,} requests)",
            out=results_dir / f"a2_bar_n{n}.png",
        )

    # Summary line chart across all N values
    line_chart(
        points,
        title=f"A-2: Average Load per Server vs N ({n_requests:,} requests)",
        out=results_dir / "a2_line_chart.png",
    )

    # Persist the computed points for later reference / reporting
    summary = {"experiment": "A-2", "n_requests": n_requests, "points": points}
    summary_path = results_dir / "a2_summary.json"  
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n  Summary data -> {summary_path}")


def experiment_a3(lb_url: str, n_requests: int, concurrency: int,
                  results_dir: Path) -> None:
    """A-3: Test server failure and recovery."""
    print("\n" + "=" * 60)
    print("  EXPERIMENT A-3: Server failure and recovery test")
    print("=" * 60)
    
    print("  Note: A-3 requires the real LB and Docker manager to kill containers.")
    print("  Orchestration: ")
    print("  1. Ensure N=3 servers are running.")
    print("  2. Send requests, and during the run, manually kill a container or")
    print("     have the script call a mock endpoint to kill it.")
    print("  3. Verify the LB's heartbeat replaces the dead container.")
    
    set_server_count(lb_url, 3)
    # We can run a load test here, but killing a container from outside
    # needs Docker SDK or a custom endpoint. We will just run a basic test.
    csv_path = results_dir / "a3_n3_recovery.csv"
    print(f"\n  Sending {n_requests:,} requests to {lb_url}/home ...")
    asyncio.run(run_load_test(
        url=f"{lb_url}/home", n=n_requests,
        concurrency=concurrency, out_path=csv_path,
    ))
    rows = load_csv(csv_path)
    _print_distribution_summary(rows)


def experiment_a4(lb_url: str, n_requests: int, concurrency: int,
                  results_dir: Path) -> None:
    """A-4: Re-run A-1 and A-2 after modifying hash functions."""
    print("\n" + "=" * 60)
    print("  EXPERIMENT A-4: Modified Hash Functions")
    print("=" * 60)
    
    print("  Note: Ensure Person B has modified the hash functions H(i) and Phi(i, j)")
    print("  in consistent_hash.py before running this.")
    
    a4_dir = results_dir / "a4_results"
    a4_dir.mkdir(parents=True, exist_ok=True)
    
    # Run A-1 equivalent
    print("\n  --- A-4 (Part 1: like A-1) ---")
    set_server_count(lb_url, 3)
    csv_path_a1 = a4_dir / "a4_n3.csv"
    asyncio.run(run_load_test(
        url=f"{lb_url}/home", n=n_requests,
        concurrency=concurrency, out_path=csv_path_a1,
    ))
    rows_a1 = load_csv(csv_path_a1)
    bar_chart(
        rows_a1,
        title=f"A-4: Request Distribution (N=3, {n_requests:,} requests)",
        out=a4_dir / "a4_bar_chart.png",
    )
    
    # Run A-2 equivalent
    print("\n  --- A-4 (Part 2: like A-2) ---")
    points: list[tuple[int, float]] = []
    for n in range(2, 7):
        set_server_count(lb_url, n)
        time.sleep(0.3)
        csv_path_a2 = a4_dir / f"a4_n{n}.csv"
        asyncio.run(run_load_test(
            url=f"{lb_url}/home", n=n_requests,
            concurrency=concurrency, out_path=csv_path_a2,
        ))
        rows_a2 = load_csv(csv_path_a2)
        ok_rows = [r for r in rows_a2 if r["ok"] == "True"]
        avg_load = len(ok_rows) / n if n else 0
        points.append((n, avg_load))
        
        bar_chart(
            rows_a2,
            title=f"A-4: Distribution (N={n}, {n_requests:,} requests)",
            out=a4_dir / f"a4_bar_n{n}.png",
        )
        
    line_chart(
        points,
        title=f"A-4: Average Load per Server vs N ({n_requests:,} requests)",
        out=a4_dir / "a4_line_chart.png",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_distribution_summary(rows: list[dict]) -> None:
    """Quick console summary of request distribution."""
    ok = [r for r in rows if r["ok"] == "True"]
    counts = Counter(r["server_id"] for r in ok)
    total = len(ok)  
    print(f"\n  Distribution ({total:,} successful requests):")
    try:
        items = sorted(counts.items(), key=lambda x: int(x[0]))
    except ValueError:
        items = sorted(counts.items())
    for sid, cnt in items:
        pct = cnt / total * 100 if total else 0
        bar = "#" * int(pct / 2)
        print(f"    Server {sid:>6s}: {cnt:>6,} ({pct:5.1f}%) {bar}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Run Task 4 load-balancer experiments (Person D).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--lb-url", default="http://localhost:5000",
                   help="Base URL of the load balancer (default: http://localhost:5000)")
    p.add_argument("--n-requests", type=int, default=10_000,
                   help="Requests to send per sub-experiment (default: 10 000)")
    p.add_argument("--concurrency", type=int, default=200,
                   help="Max concurrent connections (default: 200)")
    p.add_argument("--results-dir", default="results",
                   help="Output directory for CSVs and PNGs (default: results/)")
    p.add_argument("--experiment", choices=["a1", "a2", "a3", "a4", "all"], default="all",
                   help="Which experiment to run (default: all)")
    args = p.parse_args()

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"Load Balancer : {args.lb_url}")
    print(f"Requests/exp  : {args.n_requests:,}")
    print(f"Concurrency   : {args.concurrency}")
    print(f"Results dir   : {results_dir.resolve()}")

    # Verify the LB is reachable
    try:
        rep = get_replicas(args.lb_url)
        print(f"LB status     : UP  (N={rep['message']['N']}, "
              f"replicas={rep['message']['replicas']})")
    except (urllib.error.URLError, ConnectionError) as exc:
        print(f"\nERROR: Cannot reach LB at {args.lb_url}")
        print("  Start the stub LB first:")
        print("    cd ../loadbalancer && python stub_lb.py")
        print(f"\n  ({exc})")
        sys.exit(1)

    # Run requested experiments
    if args.experiment in ("a1", "all"):
        experiment_a1(args.lb_url, args.n_requests, args.concurrency, results_dir)

    if args.experiment in ("a2", "all"):
        experiment_a2(args.lb_url, args.n_requests, args.concurrency, results_dir)
        
    if args.experiment in ("a3", "all"):
        experiment_a3(args.lb_url, args.n_requests, args.concurrency, results_dir)
        
    if args.experiment in ("a4", "all"):
        experiment_a4(args.lb_url, args.n_requests, args.concurrency, results_dir)

    print("\n" + "=" * 60)
    print("  ALL EXPERIMENTS COMPLETE")
    print(f"  Results -> {results_dir.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
