"""
Chart generation for Task 4. See docs/TEAM.md section 5 (Person D).

Two chart types needed:
  bar  -> per-server request counts (experiments A-1, A-4)
  line -> average load vs N (experiments A-2, A-4)
"""
import argparse
import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


def load_csv(path: Path):
    with path.open() as f:
        return list(csv.DictReader(f))


def bar_chart(rows, title: str, out: Path):
    """Bar chart of request count per server. Used for A-1 and A-4."""
    counts = Counter(r["server_id"] for r in rows if r["ok"] == "True")
    # TODO Person D: sort by server_id, draw bars, label axes (server_id,
    # request_count), title=title, save to out (PNG).
    raise NotImplementedError("Person D: implement bar_chart")


def line_chart(points, title: str, out: Path):
    """Line chart of average load per server vs N. Used for A-2 and A-4.

    `points` is a list of (N, avg_load_per_server) tuples.
    """
    # TODO Person D: plot points, x="N (number of servers)",
    # y="avg requests per server", title=title, save to out (PNG).
    raise NotImplementedError("Person D: implement line_chart")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True, help="raw_data.csv produced by load_test.py")
    p.add_argument("--out", required=True, help="output PNG path")
    p.add_argument("--type", choices=["bar", "line"], required=True)
    p.add_argument("--title", default="")
    args = p.parse_args()
    rows = load_csv(Path(args.csv))
    if args.type == "bar":
        bar_chart(rows, args.title or "Requests per server", Path(args.out))
    else:
        # line_chart requires (N, avg_load) tuples - typically built by an
        # orchestration script that runs load_test.py at multiple N values.
        raise SystemExit("line_chart needs an orchestration step; see TEAM.md A-2")
