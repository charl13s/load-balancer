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

import matplotlib
matplotlib.use("Agg")  # non-interactive backend so it works headless / in Docker
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Styling defaults — professional look without relying on optional style packs
# ---------------------------------------------------------------------------
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "#f9f9f9",
    "axes.edgecolor": "#cccccc",
    "axes.grid": True,
    "grid.color": "#e0e0e0",
    "grid.linewidth": 0.7,
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
})

# Colour palette — distinguishable but not garish
BAR_COLOURS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
    "#9c755f", "#bab0ac",
]


def load_csv(path: Path):
    with path.open() as f:
        return list(csv.DictReader(f))


def bar_chart(rows, title: str, out: Path):
    """Bar chart of request count per server. Used for A-1 and A-4."""
    counts = Counter(r["server_id"] for r in rows if r["ok"] == "True")
    if not counts:
        print(f"WARNING: no successful requests in data — skipping {out}")
        return

    # Sort by server_id (try numeric first, fall back to lexicographic)
    try:
        sorted_items = sorted(counts.items(), key=lambda x: int(x[0]))
    except ValueError:
        sorted_items = sorted(counts.items())

    server_ids = [str(item[0]) for item in sorted_items]
    request_counts = [item[1] for item in sorted_items]
    total = sum(request_counts)

    fig, ax = plt.subplots(figsize=(max(8, len(server_ids) * 1.5), 6))
    colours = [BAR_COLOURS[i % len(BAR_COLOURS)] for i in range(len(server_ids))]
    bars = ax.bar(server_ids, request_counts, color=colours,
                  edgecolor="white", linewidth=1.2, width=0.6)

    ax.set_xlabel("Server ID")
    ax.set_ylabel("Request Count")
    ax.set_title(title, fontweight="bold", pad=12)

    # Value + percentage labels above each bar
    y_max = max(request_counts)
    for bar, count in zip(bars, request_counts):
        pct = count / total * 100
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + y_max * 0.015,
            f"{count}\n({pct:.1f}%)",
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )

    ax.set_ylim(0, y_max * 1.18)  # room for labels
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved bar chart -> {out}")


def line_chart(points, title: str, out: Path):
    """Line chart of average load per server vs N. Used for A-2 and A-4.

    `points` is a list of (N, avg_load_per_server) tuples.
    """
    if not points:
        print(f"WARNING: no data points — skipping {out}")
        return

    points_sorted = sorted(points, key=lambda x: x[0])
    ns = [p[0] for p in points_sorted]
    avgs = [p[1] for p in points_sorted]

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(ns, avgs, marker="o", linewidth=2.5, markersize=10,
            color="#4e79a7", markeredgecolor="white", markeredgewidth=2,
            zorder=5)

    # Fill under the line for visual weight
    ax.fill_between(ns, avgs, alpha=0.08, color="#4e79a7")

    # Annotate each point with the value
    for n, avg in zip(ns, avgs):
        ax.annotate(
            f"{avg:,.0f}",
            (n, avg),
            textcoords="offset points",
            xytext=(0, 14),
            ha="center", fontweight="bold", fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cccccc", lw=0.8),
        )

    ax.set_xlabel("N (number of servers)")
    ax.set_ylabel("Average Requests per Server")
    ax.set_title(title, fontweight="bold", pad=12)
    ax.set_xticks(ns)

    plt.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved line chart -> {out}")


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
        # line_chart requires (N, avg_load) tuples - typically built by
        # run_experiments.py which runs load_test.py at multiple N values.
        raise SystemExit("line_chart needs an orchestration step — use run_experiments.py")
