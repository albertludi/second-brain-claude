"""Generate the second-brain-claude statistics infographic (v3).

Produces a 1200x2600 PNG at 100 dpi with four stacked panels:
    1. Hero stat (mean token savings)
    2. Per-query bar chart
    3. Scaling line chart
    4. Monthly summary

Run:
    python3 scripts/generate_infographic.py
"""

from __future__ import annotations

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec

# ---------------------------------------------------------------------------
# Style tokens
# ---------------------------------------------------------------------------
BG = "#0d1117"  # GitHub dark background
PANEL_BG = "#0d1117"  # keep panels flush with canvas
ACCENT = "#58a6ff"  # GitHub blue
ACCENT2 = "#3fb950"  # GitHub green
WARN = "#f0883e"  # muted orange for low ratios
TEXT = "#f0f6fc"  # primary text (near white)
MUTED = "#8b949e"  # secondary text (light gray)
GRID = "#21262d"  # subtle grid / separators

LOW_COLOR = "#f85149"  # red-orange for <4x
LOW_COLOR_ALT = WARN  # orange accent
MID_COLOR = ACCENT  # blue for 4-8x
HIGH_COLOR = ACCENT2  # green for >8x


def color_for_ratio(r: float) -> str:
    if r < 4:
        return LOW_COLOR_ALT
    if r <= 8:
        return MID_COLOR
    return HIGH_COLOR


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
PER_QUERY = [
    ("project_overview", 2.50),
    ("writing_feedback", 3.11),
    ("multi_file_analysis", 4.00),
    ("gravity_model_spec", 5.20),
    ("network_analysis_q", 6.00),
    ("git_workflow", 6.50),
    ("latex_compilation", 7.00),
    ("paper_structure", 7.50),
    ("stata_package_query", 8.00),
    ("reference_did_syntax", 9.00),
    ("tool_lookup", 10.50),
    ("style_preferences", 12.00),
]

SCALING = [
    (10, 6.8),
    (20, 8.8),
    (30, 10.0),
    (50, 11.5),
    (75, 12.7),
    (100, 13.6),
]

MEAN_RATIO = 6.78
CI_LOW = 5.27
CI_HIGH = 8.39
N_QUERIES = 12
N_BOOTSTRAP = 1000
MONTHLY_TOKENS_TEXT = "~1.49M tokens saved per month"
MONTHLY_SUB = "(5 queries/day \u00d7 30 days, ~10,500 tokens avg)"
REPRO_FOOT = "Reproduce: python3 scripts/bootstrap_token_analysis.py"

OUT_PATH = "/tmp/second-brain-clone/docs/images/infographic_v3.png"


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------
def style_axes(ax, spines_bottom_left_only: bool = True) -> None:
    ax.set_facecolor(PANEL_BG)
    for name, spine in ax.spines.items():
        if spines_bottom_left_only and name in ("top", "right"):
            spine.set_visible(False)
        else:
            spine.set_color(GRID)
            spine.set_linewidth(0.8)
    ax.tick_params(colors=MUTED, labelsize=11, length=0)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def draw_panel_divider(fig, y: float) -> None:
    """Thin horizontal divider drawn in figure coordinates (0..1)."""
    fig.add_artist(
        plt.Line2D([0.06, 0.94], [y, y], color=GRID, linewidth=0.8, alpha=0.9)
    )


# ---------------------------------------------------------------------------
# Panel builders
# ---------------------------------------------------------------------------
def panel_hero(ax) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Small eyebrow label
    ax.text(
        0.5,
        0.88,
        "SECOND-BRAIN-CLAUDE  \u00b7  TOKEN EFFICIENCY",
        ha="center",
        va="center",
        color=MUTED,
        fontsize=13,
        fontweight="bold",
        family="DejaVu Sans",
    )

    # Giant hero number
    ax.text(
        0.5,
        0.55,
        f"{MEAN_RATIO:.2f}\u00d7",
        ha="center",
        va="center",
        color=ACCENT,
        fontsize=150,
        fontweight="bold",
        family="DejaVu Sans",
    )

    # Subtitle
    ax.text(
        0.5,
        0.26,
        "fewer tokens per query",
        ha="center",
        va="center",
        color=TEXT,
        fontsize=26,
        fontweight="semibold",
        family="DejaVu Sans",
    )

    # Sub-subtitle (CI + sample info)
    ci_line = (
        f"95% CI: {CI_LOW:.2f}\u00d7 \u2013 {CI_HIGH:.2f}\u00d7   \u00b7   "
        f"n={N_QUERIES} queries   \u00b7   {N_BOOTSTRAP:,} bootstrap resamples"
    )
    ax.text(
        0.5,
        0.12,
        ci_line,
        ha="center",
        va="center",
        color=MUTED,
        fontsize=14,
        family="DejaVu Sans",
    )


def panel_per_query(ax) -> None:
    style_axes(ax)
    labels = [name for name, _ in PER_QUERY]
    values = [val for _, val in PER_QUERY]
    colors = [color_for_ratio(v) for v in values]

    # Sort ascending so largest appears at the top
    order = np.argsort(values)
    labels = [labels[i] for i in order]
    values = [values[i] for i in order]
    colors = [colors[i] for i in order]

    y = np.arange(len(labels))
    bars = ax.barh(y, values, color=colors, edgecolor="none", height=0.62)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=TEXT, fontsize=12)
    ax.set_xlim(0, max(values) * 1.18)
    ax.set_xlabel(
        "Token savings ratio (baseline / second-brain)", color=MUTED, fontsize=12
    )

    # Title
    ax.set_title(
        "Token savings by query type",
        color=TEXT,
        fontsize=20,
        fontweight="bold",
        loc="left",
        pad=18,
    )

    # Annotate bar values
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.2f}\u00d7",
            va="center",
            ha="left",
            color=TEXT,
            fontsize=11,
            fontweight="bold",
        )

    # Light vertical gridlines behind bars
    ax.xaxis.grid(True, color=GRID, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)

    # Legend for color bands
    legend_x = 0.985
    legend_y0 = 1.06
    legend_items = [
        ("<4\u00d7", LOW_COLOR_ALT),
        ("4\u20138\u00d7", MID_COLOR),
        (">8\u00d7", HIGH_COLOR),
    ]
    for i, (lbl, col) in enumerate(legend_items):
        ax.scatter(
            [legend_x - 0.11 + i * 0.055],
            [legend_y0],
            transform=ax.transAxes,
            color=col,
            s=120,
            marker="s",
            clip_on=False,
        )
        ax.text(
            legend_x - 0.085 + i * 0.055,
            legend_y0,
            lbl,
            transform=ax.transAxes,
            color=MUTED,
            fontsize=11,
            va="center",
        )


def panel_scaling(ax) -> None:
    style_axes(ax)
    xs = np.array([n for n, _ in SCALING])
    ys = np.array([r for _, r in SCALING])

    # Smooth curve through the log-style projection points
    x_smooth = np.linspace(xs.min(), xs.max(), 200)
    # Interpolate on log scale for a visually smooth curve
    y_smooth = np.interp(np.log(x_smooth), np.log(xs), ys)

    ax.plot(
        x_smooth,
        y_smooth,
        color=ACCENT,
        linewidth=3.0,
        alpha=0.95,
        zorder=2,
    )
    # Subtle fill under the curve
    ax.fill_between(
        x_smooth,
        y_smooth,
        ys.min() * 0.85,
        color=ACCENT,
        alpha=0.10,
        zorder=1,
    )
    # Markers at measured projection points
    ax.scatter(
        xs,
        ys,
        s=90,
        color=ACCENT,
        edgecolor=BG,
        linewidth=2.0,
        zorder=3,
    )

    # Dashed vertical line at the current measurement point (x=10)
    ax.axvline(10, color=MUTED, linestyle="--", linewidth=1.3, alpha=0.8, zorder=1)
    ax.text(
        10,
        ys.max() * 1.02,
        "current (10 files)",
        rotation=90,
        color=MUTED,
        fontsize=11,
        ha="right",
        va="top",
    )

    # Annotate 50-file point
    idx_50 = int(np.where(xs == 50)[0][0])
    ax.scatter(
        [xs[idx_50]],
        [ys[idx_50]],
        s=180,
        color=ACCENT2,
        edgecolor=BG,
        linewidth=2.0,
        zorder=4,
    )
    ax.annotate(
        f"{ys[idx_50]:.1f}\u00d7 at 50 files",
        xy=(xs[idx_50], ys[idx_50]),
        xytext=(xs[idx_50] + 8, ys[idx_50] - 2.0),
        color=ACCENT2,
        fontsize=13,
        fontweight="bold",
        arrowprops=dict(
            arrowstyle="-",
            color=ACCENT2,
            linewidth=1.2,
            alpha=0.8,
        ),
    )

    ax.set_xticks(xs)
    ax.set_xticklabels([str(x) for x in xs])
    ax.set_xlabel("Number of memory files", color=MUTED, fontsize=12)
    ax.set_ylabel("Projected token savings ratio", color=MUTED, fontsize=12)
    ax.set_ylim(ys.min() * 0.85, ys.max() * 1.18)
    ax.set_xlim(xs.min() - 4, xs.max() + 6)

    ax.yaxis.grid(True, color=GRID, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)

    ax.set_title(
        "Savings grow with memory size",
        color=TEXT,
        fontsize=20,
        fontweight="bold",
        loc="left",
        pad=18,
    )


def panel_summary(ax) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(
        0.5,
        0.78,
        MONTHLY_TOKENS_TEXT,
        ha="center",
        va="center",
        color=ACCENT2,
        fontsize=36,
        fontweight="bold",
        family="DejaVu Sans",
    )
    ax.text(
        0.5,
        0.50,
        MONTHLY_SUB,
        ha="center",
        va="center",
        color=TEXT,
        fontsize=18,
        family="DejaVu Sans",
    )
    ax.text(
        0.5,
        0.22,
        REPRO_FOOT,
        ha="center",
        va="center",
        color=MUTED,
        fontsize=12,
        style="italic",
        family="DejaVu Sans",
    )


# ---------------------------------------------------------------------------
# Assemble figure
# ---------------------------------------------------------------------------
def build_figure() -> plt.Figure:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": GRID,
            "axes.labelcolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "text.color": TEXT,
        }
    )

    # 12 x 26 inches at 100 dpi -> 1200 x 2600 px
    fig = plt.figure(figsize=(12, 26), dpi=100, facecolor=BG)

    # Panel height weights: 30 / 25 / 25 / 20
    gs = GridSpec(
        nrows=4,
        ncols=1,
        height_ratios=[30, 25, 25, 20],
        left=0.22,
        right=0.94,
        top=0.97,
        bottom=0.03,
        hspace=0.32,
    )

    ax_hero = fig.add_subplot(gs[0, 0])
    ax_bars = fig.add_subplot(gs[1, 0])
    ax_line = fig.add_subplot(gs[2, 0])
    ax_sum = fig.add_subplot(gs[3, 0])

    panel_hero(ax_hero)
    panel_per_query(ax_bars)
    panel_scaling(ax_line)
    panel_summary(ax_sum)

    # Subtle dividers between panels
    # Figure-coordinate y-positions approximately between gridspec rows.
    # Heights sum to 100 over the usable vertical range [0.03, 0.97] = 0.94.
    top, bottom = 0.97, 0.03
    total = 30 + 25 + 25 + 20

    def yline(cum_top_units: float) -> float:
        return top - (cum_top_units / total) * (top - bottom)

    # We do not draw dividers in the gutters for now — hspace gives breathing room.
    # (Kept helper for future tweaks.)
    _ = yline

    return fig


def main() -> None:
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    fig = build_figure()
    fig.savefig(
        OUT_PATH,
        dpi=100,
        facecolor=BG,
        edgecolor="none",
    )
    plt.close(fig)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
