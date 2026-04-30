"""
visualization.py
Visualization Module - Generates charts using matplotlib
"""

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import numpy as np


# ── Color palette ──────────────────────────────────────────────────────────────
ALGO_COLORS = {
    "FCFS":   "#378ADD",
    "SSTF":   "#1D9E75",
    "SCAN":   "#D85A30",
    "C-SCAN": "#D4537E",
    "LOOK":   "#9B59B6",
    "C-LOOK": "#E67E22",
}

DARK_BG      = "#1e1e2e"
PANEL_BG     = "#2a2a3e"
TEXT_COLOR   = "#e0e0ef"
GRID_COLOR   = "#3a3a5e"
ACCENT       = "#7c7cff"


def _apply_dark_style(ax, fig):
    """Apply dark theme to a matplotlib axes & figure."""
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(PANEL_BG)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.grid(True, color=GRID_COLOR, linestyle="--", linewidth=0.5, alpha=0.7)


def plot_seek(sequence: list[int], algo_name: str,
              total_seek: int, disk_size: int = 200,
              embed_fig: Figure = None) -> Figure:
    """
    Plot head movement for a single algorithm.
    If embed_fig is given, draws into it (for embedding in GUI).
    Returns the Figure.
    """
    fig = embed_fig or Figure(figsize=(9, 5), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)

    color = ALGO_COLORS.get(algo_name, ACCENT)
    steps = list(range(len(sequence)))

    # Shaded area under curve
    ax.fill_between(steps, sequence, alpha=0.08, color=color)

    # Main line
    ax.plot(steps, sequence, color=color, linewidth=2.2, zorder=3,
            marker="o", markersize=6, markerfacecolor="white",
            markeredgecolor=color, markeredgewidth=1.8)

    # Label each point
    for i, (x, y) in enumerate(zip(steps, sequence)):
        offset = 8 if i % 2 == 0 else -14
        ax.annotate(str(y), xy=(x, y), xytext=(0, offset),
                    textcoords="offset points", ha="center",
                    fontsize=8, color=TEXT_COLOR, fontweight="bold")

    # Highlight start position
    ax.plot(0, sequence[0], "s", color="#FFD700", markersize=9, zorder=5,
            label=f"Start: {sequence[0]}")

    ax.set_title(f"{algo_name}  —  Total Seek: {total_seek} cylinders",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Step (service order)", fontsize=10)
    ax.set_ylabel("Cylinder position", fontsize=10)
    ax.set_xlim(-0.5, len(steps) - 0.5)
    ax.set_ylim(-5, disk_size + 5)
    ax.set_xticks(steps)
    ax.legend(fontsize=9, facecolor=PANEL_BG, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR)

    _apply_dark_style(ax, fig)
    fig.tight_layout(pad=1.5)
    return fig


def plot_comparison(results: dict, embed_fig: Figure = None) -> Figure:
    """
    Bar chart comparing all algorithms' total seek times.
    Highlights the best (lowest) algorithm in gold.
    Returns the Figure.
    """
    fig = embed_fig or Figure(figsize=(9, 5), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)

    names = list(results.keys())
    totals = [results[n]["total"] for n in names]
    best_idx = totals.index(min(totals))

    bar_colors = [ALGO_COLORS.get(n, ACCENT) for n in names]
    bar_colors[best_idx] = "#FFD700"  # Gold for best

    bars = ax.bar(names, totals, color=bar_colors, edgecolor="white",
                  linewidth=0.6, width=0.55, zorder=3)

    # Value labels on bars
    for bar, val in zip(bars, totals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(totals) * 0.01,
                str(val), ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=TEXT_COLOR)

    # "Best" annotation
    best_bar = bars[best_idx]
    ax.annotate("★ Best", xy=(best_bar.get_x() + best_bar.get_width() / 2,
                               best_bar.get_height()),
                xytext=(0, 22), textcoords="offset points",
                ha="center", fontsize=9, color="#FFD700", fontweight="bold",
                arrowprops=dict(arrowstyle="-", color="#FFD700", lw=1.2))

    ax.set_title("Algorithm Comparison — Total Seek Distance", fontsize=13,
                 fontweight="bold", pad=12)
    ax.set_xlabel("Algorithm", fontsize=10)
    ax.set_ylabel("Total seek distance (cylinders)", fontsize=10)
    ax.set_ylim(0, max(totals) * 1.2)
    _apply_dark_style(ax, fig)
    fig.tight_layout(pad=1.5)
    return fig


def plot_efficiency(results: dict, embed_fig: Figure = None) -> Figure:
    """
    Horizontal bar chart showing relative efficiency (%).
    Best algorithm = 100%, others scaled proportionally.
    """
    fig = embed_fig or Figure(figsize=(9, 4), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)

    names = list(results.keys())
    totals = [results[n]["total"] for n in names]
    min_seek = min(totals)
    efficiencies = [round((min_seek / t) * 100, 1) for t in totals]

    # Sort by efficiency descending
    paired = sorted(zip(efficiencies, names), reverse=True)
    efficiencies, names = zip(*paired)

    colors = [ALGO_COLORS.get(n, ACCENT) for n in names]
    colors = list(colors)
    colors[0] = "#FFD700"  # Best is first after sort

    bars = ax.barh(names, efficiencies, color=colors,
                   edgecolor="white", linewidth=0.5, height=0.5)

    for bar, val in zip(bars, efficiencies):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val}%", va="center", fontsize=9,
                fontweight="bold", color=TEXT_COLOR)

    ax.set_xlim(0, 115)
    ax.set_title("Performance Efficiency (relative to best)", fontsize=13,
                 fontweight="bold", pad=12)
    ax.set_xlabel("Efficiency (%)", fontsize=10)
    _apply_dark_style(ax, fig)
    fig.tight_layout(pad=1.5)
    return fig


def plot_all_on_one(results: dict, disk_size: int = 200,
                    embed_fig: Figure = None) -> Figure:
    """
    Overlay all algorithm paths on a single chart for comparison.
    """
    fig = embed_fig or Figure(figsize=(10, 5), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)

    max_len = max(len(v["sequence"]) for v in results.values())

    for name, data in results.items():
        seq = data["sequence"]
        steps = list(range(len(seq)))
        color = ALGO_COLORS.get(name, ACCENT)
        ax.plot(steps, seq, color=color, linewidth=1.8,
                marker="o", markersize=3.5, label=f"{name} ({data['total']})")

    ax.set_title("All Algorithms — Head Movement Overlay", fontsize=13,
                 fontweight="bold", pad=12)
    ax.set_xlabel("Step", fontsize=10)
    ax.set_ylabel("Cylinder position", fontsize=10)
    ax.set_ylim(-5, disk_size + 5)
    ax.legend(fontsize=8.5, facecolor=PANEL_BG, edgecolor=GRID_COLOR,
              labelcolor=TEXT_COLOR, ncol=2)
    _apply_dark_style(ax, fig)
    fig.tight_layout(pad=1.5)
    return fig


def save_figure(fig: Figure, path: str) -> None:
    """Save a matplotlib figure to disk as PNG."""
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
