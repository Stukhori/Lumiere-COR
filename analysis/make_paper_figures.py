"""Generate all manuscript figures, tables, captions, and analysis summary.

Run from the repository root after validation:
    python analysis/make_paper_figures.py
"""

from __future__ import annotations

from pathlib import Path
import sys
import textwrap

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd
import seaborn as sns

from rebound_common import (
    AUDIT_FILE,
    BALL_LABEL,
    BALL_ORDER,
    FIGURE_DIR,
    MASTER_FILE,
    PAPER_DIR,
    SESSION2_FILE,
    TABLE_DIR,
    TEMP_ORDER,
    audit_stats,
    ball_condition_means,
    ensure_output_dirs,
    load_data,
    matched_contrasts,
    overall_from_ball_means,
    validate_frames,
    write_validation_report,
)


BALL_COLORS = {"Ball_A": "#0072B2", "Ball_B": "#E69F00", "Ball_C": "#009E73"}
PRESSURE_COLORS = {6: "#0072B2", 10: "#D55E00", 14: "#009E73"}
PRESSURE_MARKERS = {6: "o", 10: "s", 14: "^"}
PATH_STYLES = {
    "Sealed Session 1": "-",
    "Matched Session 1": "--",
    "Matched Session 2": "-.",
}
PATH_COLORS = {
    "Sealed Session 1": "#333333",
    "Matched Session 1": "#0072B2",
    "Matched Session 2": "#CC79A7",
}


def configure_style() -> None:
    sns.set_theme(style="white", context="paper")
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "axes.linewidth": 0.8,
            "xtick.direction": "out",
            "ytick.direction": "out",
            "xtick.major.size": 3.5,
            "ytick.major.size": 3.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.12, 1.04, f"({label})", transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def finish_axis(ax: plt.Axes, horizontal_grid: bool = True) -> None:
    sns.despine(ax=ax)
    ax.grid(False)
    if horizontal_grid:
        ax.yaxis.grid(True, color="#D9D9D9", linewidth=0.55, alpha=0.8, zorder=0)
    ax.tick_params(direction="out")


def save_figure(fig: plt.Figure, stem: str) -> list[Path]:
    outputs: list[Path] = []
    for suffix in ("pdf", "svg", "png"):
        path = FIGURE_DIR / f"{stem}.{suffix}"
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.04}
        if suffix == "png":
            kwargs["dpi"] = 600
        fig.savefig(path, **kwargs)
        outputs.append(path)
    plt.close(fig)
    return outputs


def deterministic_jitter(ids: pd.Series, width: float = 0.55) -> np.ndarray:
    values = ids.to_numpy(dtype=int)
    return (((values * 37) % 101) / 100.0 - 0.5) * width


def figure1_design(master: pd.DataFrame, session2: pd.DataFrame) -> list[Path]:
    sealed = master.loc[master["Protocol"].eq("Factorial_3x3_Sealed")]
    matched = master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")]
    exp2 = session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")]
    controls = session2.loc[session2["Protocol"].eq("Baseline_Control")]

    fig, axes = plt.subplots(1, 3, figsize=(7.15, 2.65), gridspec_kw={"wspace": 0.28})
    blocks = [
        (axes[0], sealed, "Session 1: sealed factorial", "a"),
        (axes[1], matched, "Session 1: matched pressure", "b"),
        (axes[2], exp2, "Session 2: counterbalanced", "c"),
    ]
    for ax, _, heading, lab in blocks:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        panel_label(ax, lab)
        ax.text(0.5, 0.96, heading, ha="center", va="top", fontweight="bold", fontsize=8.7)

    ax = axes[0]
    temps = sorted(sealed["Target_Temp_C"].unique())
    pressures = sorted(sealed["Target_Press_PSI"].unique())
    x0, y0, cellw, cellh = 0.20, 0.24, 0.23, 0.16
    for j, temp in enumerate(temps):
        ax.text(x0 + j * cellw + cellw / 2, 0.82, f"{temp}°C", ha="center", va="center")
    for i, pressure in enumerate(pressures):
        ax.text(0.13, y0 + (2 - i) * cellh + cellh / 2, f"{pressure} PSI", ha="right", va="center")
        for j, temp in enumerate(temps):
            n = len(sealed.loc[(sealed["Target_Press_PSI"].eq(pressure)) & (sealed["Target_Temp_C"].eq(temp))])
            rect = Rectangle((x0 + j * cellw, y0 + (2 - i) * cellh), cellw * 0.86, cellh * 0.78,
                             facecolor=PRESSURE_COLORS[pressure], alpha=0.17, edgecolor=PRESSURE_COLORS[pressure], linewidth=0.8)
            ax.add_patch(rect)
            ax.text(x0 + j * cellw + cellw * 0.43, y0 + (2 - i) * cellh + cellh * 0.39,
                    f"n={n}\n(3×{n // 3})", ha="center", va="center", fontsize=6.5)
    ax.text(0.5, 0.18, "Each cell: 3 balls × 5 repeated drops", ha="center", fontsize=6.5)
    ax.text(0.5, 0.09, f"N = {len(sealed)} drops", ha="center", fontweight="bold")

    ax = axes[1]
    temps = sorted(matched["Target_Temp_C"].unique())
    for j, temp in enumerate(temps):
        x = 0.18 + j * 0.31
        n = len(matched.loc[matched["Target_Temp_C"].eq(temp)])
        box = FancyBboxPatch((x - 0.11, 0.37), 0.22, 0.27, boxstyle="round,pad=0.02",
                             facecolor="#56B4E9", alpha=0.19, edgecolor="#0072B2", linewidth=0.9)
        ax.add_patch(box)
        ax.text(x, 0.70, f"{temp}°C", ha="center", fontweight="bold")
        ax.text(x, 0.505, f"≈10 PSI\nn={n}\n(3×{n // 3})", ha="center", va="center", fontsize=6.5)
    ax.text(0.5, 0.31, "Each temperature: 3 balls × 3 repeated drops", ha="center", fontsize=6.3)
    ax.annotate("", xy=(0.80, 0.24), xytext=(0.20, 0.24), arrowprops={"arrowstyle": "<->", "color": "#777777"})
    pressure_range = matched["Pre_Impact_Press_PSI"].agg(["min", "max"])
    ax.text(0.5, 0.17, f"Measured: {pressure_range['min']:.2f}–{pressure_range['max']:.2f} PSI", ha="center", fontsize=7)
    ax.text(0.5, 0.07, f"N = {len(matched)} drops", ha="center", fontweight="bold")

    ax = axes[2]
    order = (
        exp2.sort_values("Drop_ID")
        .drop_duplicates(["Ball_ID", "Target_Temp_C"])
        .groupby("Ball_ID", sort=False)["Target_Temp_C"]
        .apply(list)
    )
    y_positions = [0.70, 0.50, 0.30]
    for ball, y in zip(BALL_ORDER, y_positions):
        sequence = order.loc[ball]
        ax.text(0.08, y, BALL_LABEL[ball], ha="left", va="center", color=BALL_COLORS[ball], fontweight="bold")
        for j, temp in enumerate(sequence):
            x = 0.40 + 0.25 * j
            circle = plt.Circle((x, y), 0.075, facecolor=BALL_COLORS[ball], alpha=0.16, edgecolor=BALL_COLORS[ball], linewidth=0.8)
            ax.add_patch(circle)
            ax.text(x, y, f"{temp}°", ha="center", va="center", fontsize=7)
            if j < len(sequence) - 1:
                ax.annotate("", xy=(x + 0.17, y), xytext=(x + 0.08, y), arrowprops={"arrowstyle": "->", "lw": 0.7, "color": "#666666"})
    ax.text(0.5, 0.12, f"{len(exp2)} experimental drops + {len(controls)} operational checks", ha="center", fontsize=7.4, fontweight="bold")
    fig.subplots_adjust(left=0.035, right=0.99, top=0.95, bottom=0.04)
    return save_figure(fig, "fig1_experimental_design")


def draw_sealed_metric(
    ax: plt.Axes, sealed: pd.DataFrame, bm: pd.DataFrame, overall: pd.DataFrame, metric: str
) -> None:
    """Draw the same trial, ball, and condition summaries in either layout."""
    for pressure in sorted(sealed["Target_Press_PSI"].unique()):
        raw = sealed.loc[sealed["Target_Press_PSI"].eq(pressure)]
        points = bm.loc[bm["Target_Press_PSI"].eq(pressure)]
        line = overall.loc[overall["Target_Press_PSI"].eq(pressure)].sort_values("Target_Temp_C")
        ax.scatter(raw["Target_Temp_C"] + deterministic_jitter(raw["Drop_ID"]), raw[metric], s=7,
                   color=PRESSURE_COLORS[pressure], alpha=0.11, edgecolors="none", zorder=1)
        ax.scatter(points["Target_Temp_C"], points[metric], s=25, marker=PRESSURE_MARKERS[pressure],
                   facecolor="white", edgecolor=PRESSURE_COLORS[pressure], linewidth=0.9, alpha=0.85, zorder=3)
        ax.plot(line["Target_Temp_C"], line[metric], color=PRESSURE_COLORS[pressure],
                marker=PRESSURE_MARKERS[pressure], markersize=5.5, linewidth=1.8,
                label=f"{pressure} PSI", zorder=4)


def sealed_figure_data(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sealed = master.loc[master["Protocol"].eq("Factorial_3x3_Sealed")].copy()
    bm = ball_condition_means(sealed, ["Target_Press_PSI"])
    overall = overall_from_ball_means(bm, ["Target_Temp_C", "Target_Press_PSI"])
    return sealed, bm, overall


def figure2_sealed(master: pd.DataFrame) -> list[Path]:
    sealed, bm, overall = sealed_figure_data(master)
    fig, axes = plt.subplots(2, 1, figsize=(4.9, 5.9), sharex=True)
    metrics = [
        ("Calculated_COR_e", "Coefficient of restitution, $e$", "a"),
        ("Pre_Impact_Press_PSI", "Pre-impact gauge pressure (PSI)", "b"),
    ]
    for ax, (metric, ylabel, lab) in zip(axes, metrics):
        draw_sealed_metric(ax, sealed, bm, overall, metric)
        ax.set_ylabel(ylabel)
        ax.set_xticks(TEMP_ORDER)
        if lab == "b":
            # Match panel (a)'s left edge, above the pressure-axis label.
            ax.text(-0.12, 1.16, "(b)", transform=ax.transAxes, fontsize=10,
                    fontweight="bold", va="bottom")
        else:
            panel_label(ax, lab)
        finish_axis(ax)
    axes[0].legend(
        title="Nominal pressure at\nreference condition",
        frameon=False,
        ncol=3,
        loc="lower left",
        bbox_to_anchor=(0, 1.02),
    )
    axes[1].set_xlabel("Target temperature (°C)")
    axes[0].set_ylim(0.70, 0.91)
    fig.subplots_adjust(left=0.15, right=0.98, top=0.82, bottom=0.10, hspace=0.42)
    return save_figure(fig, "fig2_sealed_factorial_response")


def figure2_sealed_parts(master: pd.DataFrame) -> list[Path]:
    """Export Figure 2's two panels as independent, self-contained graphs."""
    sealed, bm, overall = sealed_figure_data(master)
    parts = [
        ("Calculated_COR_e", "Coefficient of restitution, $e$", "a", "fig2a_sealed_factorial_cor"),
        ("Pre_Impact_Press_PSI", "Pre-impact gauge pressure (PSI)", "b", "fig2b_sealed_factorial_pressure"),
    ]
    outputs: list[Path] = []
    for metric, ylabel, label, stem in parts:
        fig, ax = plt.subplots(figsize=(4.9, 3.3))
        draw_sealed_metric(ax, sealed, bm, overall, metric)
        ax.set_xlabel("Target temperature (°C)")
        ax.set_ylabel(ylabel)
        ax.set_xticks(TEMP_ORDER)
        if label == "a":
            ax.set_ylim(0.70, 0.91)
        ax.text(-0.12, 1.14, f"({label})", transform=ax.transAxes,
                fontsize=10, fontweight="bold", va="bottom")
        ax.legend(
            title="Nominal pressure at\nreference condition",
            frameon=False,
            ncol=3,
            loc="lower left",
            bbox_to_anchor=(0, 1.02),
        )
        finish_axis(ax)
        fig.subplots_adjust(left=0.15, right=0.98, top=0.72, bottom=0.18)
        outputs += save_figure(fig, stem)
    return outputs


def figure3_matched(master: pd.DataFrame, session2: pd.DataFrame) -> list[Path]:
    s1 = master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")].copy()
    s2 = session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")].copy()
    sessions = {"Session 1": s1, "Session 2": s2}
    styles = {"Session 1": "--", "Session 2": "-."}
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.15), gridspec_kw={"width_ratios": [1.35, 1], "wspace": 0.35})
    ax = axes[0]
    for session, frame in sessions.items():
        bm = ball_condition_means(frame)
        overall = overall_from_ball_means(bm, ["Target_Temp_C"])
        for ball in BALL_ORDER:
            part = bm.loc[bm["Ball_ID"].eq(ball)].sort_values("Target_Temp_C")
            ax.plot(part["Target_Temp_C"], part["Calculated_COR_e"], color=BALL_COLORS[ball],
                    linestyle=styles[session], linewidth=1.0, alpha=0.62, marker="o", markersize=3.2)
        ax.plot(overall["Target_Temp_C"], overall["Calculated_COR_e"], color="#222222",
                linestyle=styles[session], linewidth=2.5, marker="o", markersize=5.2, zorder=5)
    ax.set_xlabel("Target temperature (°C)")
    ax.set_ylabel("Coefficient of restitution, $e$")
    ax.set_xticks(TEMP_ORDER)
    ax.set_ylim(0.775, 0.845)
    panel_label(ax, "a")
    finish_axis(ax)
    ball_handles = [Line2D([0], [0], color=BALL_COLORS[b], marker="o", lw=1.2, label=BALL_LABEL[b]) for b in BALL_ORDER]
    session_handles = [Line2D([0], [0], color="#222222", linestyle=styles[s], lw=2.2, label=s) for s in sessions]
    legend1 = ax.legend(handles=ball_handles, title="Ball-level means", frameon=False, loc="upper left", ncol=1)
    ax.add_artist(legend1)
    ax.legend(handles=session_handles, title="Session-wide mean", frameon=False, loc="lower right")

    ax = axes[1]
    contrasts = {name: matched_contrasts(frame) for name, frame in sessions.items()}
    y_map = {ball: 3 - i for i, ball in enumerate(BALL_ORDER)}
    for ball in BALL_ORDER:
        xs = [contrasts[s].loc[ball] for s in sessions]
        y = y_map[ball]
        ax.plot(xs, [y, y], color=BALL_COLORS[ball], alpha=0.55, linewidth=1.1, zorder=1)
        ax.scatter(xs[0], y, s=34, color=BALL_COLORS[ball], marker="o", zorder=3)
        ax.scatter(xs[1], y, s=40, color=BALL_COLORS[ball], marker="D", facecolor="white", linewidth=1.2, zorder=4)
    mean_y = 0.45
    for session, marker in [("Session 1", "o"), ("Session 2", "D")]:
        ax.scatter(contrasts[session].mean(), mean_y, s=75, marker=marker,
                   color="#222222" if marker == "o" else "white", edgecolor="#222222", linewidth=1.2, zorder=5)
    ax.axvline(0, color="#777777", linewidth=0.8, linestyle=":")
    ax.set_yticks([3, 2, 1, mean_y], ["Ball A", "Ball B", "Ball C", "Across-ball mean"])
    ax.set_xlabel(r"$\Delta e_{40-0}$")
    ax.set_ylim(0.05, 3.45)
    panel_label(ax, "b")
    finish_axis(ax, horizontal_grid=False)
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#222222", markeredgecolor="#222222", label="Session 1"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor="white", markeredgecolor="#222222", label="Session 2"),
    ]
    ax.legend(handles=handles, frameon=False, loc="lower right")
    fig.subplots_adjust(left=0.095, right=0.98, top=0.95, bottom=0.16)
    return save_figure(fig, "fig3_matched_pressure_replication")


def protocol_frames(master: pd.DataFrame, session2: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "Sealed Session 1": master.loc[
            master["Protocol"].eq("Factorial_3x3_Sealed") & master["Target_Press_PSI"].eq(10)
        ].copy(),
        "Matched Session 1": master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")].copy(),
        "Matched Session 2": session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")].copy(),
    }


def figure4_paths(master: pd.DataFrame, session2: pd.DataFrame) -> list[Path]:
    frames = protocol_frames(master, session2)
    fig, axes = plt.subplots(1, 3, figsize=(7.15, 3.15), gridspec_kw={"width_ratios": [1.15, 1.15, 0.85], "wspace": 0.38})
    for ax, metric, ylabel, lab in [
        (axes[0], "Calculated_COR_e", "Coefficient of restitution, $e$", "a"),
        (axes[1], "Pre_Impact_Press_PSI", "Pre-impact gauge pressure (PSI)", "b"),
    ]:
        for name, frame in frames.items():
            bm = ball_condition_means(frame)
            overall = overall_from_ball_means(bm, ["Target_Temp_C"]).sort_values("Target_Temp_C")
            for ball in BALL_ORDER:
                pts = bm.loc[bm["Ball_ID"].eq(ball)]
                ax.scatter(pts["Target_Temp_C"], pts[metric], s=18, color=BALL_COLORS[ball], alpha=0.40, zorder=2)
            ax.plot(overall["Target_Temp_C"], overall[metric], color=PATH_COLORS[name],
                    linestyle=PATH_STYLES[name], linewidth=2.0, marker="o", markersize=4.5, label=name, zorder=4)
        ax.set_xlabel("Target temperature (°C)")
        ax.set_ylabel(ylabel)
        ax.set_xticks(TEMP_ORDER)
        panel_label(ax, lab)
        finish_axis(ax)
    axes[0].set_ylim(0.77, 0.89)
    axes[0].legend(frameon=False, loc="upper left")

    ax = axes[2]
    changes = {}
    for name, frame in frames.items():
        contrast = matched_contrasts(frame)
        changes[name] = contrast
        y = list(frames).index(name)
        ax.scatter(contrast.values, np.repeat(y, len(contrast)), s=22,
                   c=[BALL_COLORS[b] for b in BALL_ORDER], alpha=0.65, zorder=2)
        ax.scatter(contrast.mean(), y, marker="D", s=60, facecolor=PATH_COLORS[name],
                   edgecolor="white", linewidth=0.7, zorder=4)
    ax.axvline(0, color="#777777", linewidth=0.8, linestyle=":")
    ax.set_yticks(range(len(frames)), [])
    for y, label in enumerate(["Sealed S1", "Matched S1", "Matched S2"]):
        ax.text(0.02, y, label, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=6.7)
    ax.set_xlabel(r"$\Delta e_{40-0}$")
    ax.invert_yaxis()
    panel_label(ax, "c")
    finish_axis(ax, horizontal_grid=False)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.95, bottom=0.17)
    return save_figure(fig, "fig4_protocol_path_comparison")


def figure5_audit(audit: pd.DataFrame) -> list[Path]:
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.1), gridspec_kw={"wspace": 0.28})
    for ax, height, label, xlab in [
        (axes[0], "h0", "a", "Mean release height (m)"),
        (axes[1], "h1", "b", "Mean rebound height (m)"),
    ]:
        a1 = audit[f"Annotator1_{height}_m"]
        a2 = audit[f"Annotator2_{height}_m"]
        x = (a1 + a2) / 2
        y = (a2 - a1) * 1000
        stats = audit_stats(audit, height)
        ax.scatter(x, y, s=25, facecolor="#56B4E9", edgecolor="#0072B2", linewidth=0.7, alpha=0.82)
        ax.axhline(stats["bias_mm"], color="#222222", linewidth=1.4, label="Mean bias")
        ax.axhline(stats["loa_low_mm"], color="#D55E00", linewidth=1.1, linestyle="--", label="95% limits of agreement")
        ax.axhline(stats["loa_high_mm"], color="#D55E00", linewidth=1.1, linestyle="--")
        ax.set_xlabel(xlab)
        ax.set_ylabel("Annotator 2 − Annotator 1 (mm)")
        annotation = (
            f"n = {stats['n']}\n"
            f"Bias = {stats['bias_mm']:+.2f} mm\n"
            f"Mean |difference| = {stats['mad_mm']:.2f} mm\n"
            f"Limits = {stats['loa_low_mm']:+.2f}, {stats['loa_high_mm']:+.2f} mm"
        )
        ax.text(0.03, 0.97, annotation, transform=ax.transAxes, ha="left", va="top", fontsize=7.2,
                bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.96, "pad": 1.5})
        panel_label(ax, label)
        finish_axis(ax)
    axes[1].legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    fig.subplots_adjust(left=0.095, right=0.985, top=0.95, bottom=0.28)
    return save_figure(fig, "fig5_annotation_agreement")


def figure_s1_release(master: pd.DataFrame, session2: pd.DataFrame) -> list[Path]:
    panels = [
        ("Session 1 sealed", master.loc[master["Protocol"].eq("Factorial_3x3_Sealed")]),
        ("Session 1 matched", master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")]),
        ("Session 2", session2),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.15, 2.65), sharey=True, gridspec_kw={"wspace": 0.18})
    for i, (ax, (name, frame)) in enumerate(zip(axes, panels)):
        for ball in BALL_ORDER:
            part = frame.loc[frame["Ball_ID"].eq(ball)]
            if name == "Session 2":
                part = part.loc[part["Protocol"].eq("Matched_Counterbalanced")]
            ax.scatter(part["Drop_ID"], part["Release_Height_m"], s=13, color=BALL_COLORS[ball], alpha=0.70, marker="o")
        if name == "Session 2":
            controls = frame.loc[frame["Protocol"].eq("Baseline_Control")]
            ax.scatter(controls["Drop_ID"], controls["Release_Height_m"], s=38, facecolors="none", edgecolors="#222222", marker="s", label="Operational check")
        ax.axhline(2.500, color="#555555", linewidth=1.0, linestyle="--")
        ax.set_title(name)
        ax.set_xlabel("Drop ID / run order")
        panel_label(ax, chr(ord("a") + i))
        finish_axis(ax)
    axes[0].set_ylabel("Release height (m)")
    axes[-1].legend(frameon=False, loc="lower right")
    fig.subplots_adjust(left=0.10, right=0.99, top=0.85, bottom=0.20)
    return save_figure(fig, "figS1_release_height_stability")


def figure_s2_pressure(master: pd.DataFrame, session2: pd.DataFrame) -> list[Path]:
    s1 = master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")].copy()
    s2 = session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")].copy()
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.0), sharey=True, gridspec_kw={"wspace": 0.12})
    for ax, frame, title, lab in [(axes[0], s1, "Session 1 matched", "a"), (axes[1], s2, "Session 2 matched", "b")]:
        for ball in BALL_ORDER:
            part = frame.loc[frame["Ball_ID"].eq(ball)]
            ax.scatter(part["Target_Temp_C"] + deterministic_jitter(part["Drop_ID"], 1.4), part["Pre_Impact_Press_PSI"],
                       s=24, color=BALL_COLORS[ball], alpha=0.72, label=BALL_LABEL[ball])
        ax.axhline(10, color="#444444", linewidth=1.1, linestyle="--", label="10 PSI reference")
        ax.set_title(title)
        ax.set_xlabel("Target temperature (°C)")
        ax.set_xticks(TEMP_ORDER)
        panel_label(ax, lab)
        finish_axis(ax)
    row161 = s1.loc[s1["Drop_ID"].eq(161)]
    if not row161.empty:
        x = float(row161["Target_Temp_C"].iloc[0] + deterministic_jitter(row161["Drop_ID"], 1.4)[0])
        y = float(row161["Pre_Impact_Press_PSI"].iloc[0])
        axes[0].annotate("Drop 161", (x, y), xytext=(-38, 18), textcoords="offset points",
                         arrowprops={"arrowstyle": "->", "lw": 0.7}, fontsize=7)
    axes[0].set_ylabel("Pre-impact gauge pressure (PSI)")
    rng = s1["Pre_Impact_Press_PSI"].agg(["min", "max"])
    axes[0].text(0.03, 0.04, f"Observed range: {rng['min']:.2f}–{rng['max']:.2f} PSI", transform=axes[0].transAxes, fontsize=7)
    handles = [Line2D([0], [0], marker="o", color="none", markerfacecolor=BALL_COLORS[b], label=BALL_LABEL[b]) for b in BALL_ORDER]
    handles.append(Line2D([0], [0], color="#444444", linestyle="--", label="10 PSI reference"))
    axes[1].legend(handles=handles, frameon=False, loc="lower right")
    fig.subplots_adjust(left=0.10, right=0.99, top=0.86, bottom=0.17)
    return save_figure(fig, "figS2_matched_pressure_control")


def residualize(frame: pd.DataFrame, condition_cols: list[str]) -> pd.DataFrame:
    out = frame.copy()
    centre = out.groupby(condition_cols, observed=True)["Calculated_COR_e"].transform("mean")
    out["COR_residual"] = out["Calculated_COR_e"] - centre
    return out


def figure_s3_run_order(master: pd.DataFrame, session2: pd.DataFrame) -> list[Path]:
    sealed = residualize(master.loc[master["Protocol"].eq("Factorial_3x3_Sealed")], ["Ball_ID", "Target_Temp_C", "Target_Press_PSI"])
    s1m = residualize(master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")], ["Ball_ID", "Target_Temp_C"])
    s2m = residualize(session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")], ["Ball_ID", "Target_Temp_C"])
    controls = session2.loc[session2["Protocol"].eq("Baseline_Control")].copy()
    controls["COR_residual"] = controls["Calculated_COR_e"] - controls["Calculated_COR_e"].mean()
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.0), sharey=True, gridspec_kw={"wspace": 0.13})
    for label, frame, marker in [("Sealed", sealed, "o"), ("Matched", s1m, "^")]:
        for ball in BALL_ORDER:
            part = frame.loc[frame["Ball_ID"].eq(ball)]
            axes[0].scatter(part["Drop_ID"], part["COR_residual"], s=13, color=BALL_COLORS[ball], alpha=0.56, marker=marker, label=label if ball == "Ball_A" else None)
    for ball in BALL_ORDER:
        part = s2m.loc[s2m["Ball_ID"].eq(ball)]
        axes[1].scatter(part["Drop_ID"], part["COR_residual"], s=18, color=BALL_COLORS[ball], alpha=0.68, marker="o")
    axes[1].scatter(controls["Drop_ID"], controls["COR_residual"], s=40, facecolor="white", edgecolor="#222222", marker="s", label="Operational checks")
    for i, (ax, title) in enumerate(zip(axes, ["Session 1", "Session 2 counterbalanced"])):
        ax.axhline(0, color="#555555", linewidth=0.9, linestyle="--")
        ax.set_title(title)
        ax.set_xlabel("Drop ID / run order")
        panel_label(ax, chr(ord("a") + i))
        finish_axis(ax)
    axes[0].set_ylabel("Within ball-condition COR residual")
    axes[0].legend(frameon=False, loc="lower right")
    axes[1].legend(frameon=False, loc="lower right")
    fig.subplots_adjust(left=0.105, right=0.99, top=0.86, bottom=0.18)
    return save_figure(fig, "figS3_run_order_diagnostics")


def latex_escape(value: object) -> str:
    text = str(value)
    for source, target in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")]:
        text = text.replace(source, target)
    return text


def write_table_pair(frame: pd.DataFrame, stem: str) -> list[Path]:
    csv_path = TABLE_DIR / f"{stem}.csv"
    tex_path = TABLE_DIR / f"{stem}.tex"
    frame.to_csv(csv_path, index=False, float_format="%.6f")
    def format_cell(value: object) -> str:
        if pd.isna(value):
            return "--"
        if isinstance(value, (float, np.floating)):
            return f"{value:.4f}"
        return latex_escape(value)

    column_spec = "l" * len(frame.columns)
    header = " & ".join(latex_escape(col) for col in frame.columns) + r" \\"
    body = [" & ".join(format_cell(value) for value in row) + r" \\" for row in frame.itertuples(index=False, name=None)]
    tex = "\n".join(
        [
            rf"\begin{{tabular}}{{{column_spec}}}",
            r"\hline",
            header,
            r"\hline",
            *body,
            r"\hline",
            r"\end{tabular}",
            "",
        ]
    )
    tex_path.write_text(tex, encoding="utf-8")
    return [csv_path, tex_path]


def make_tables(master: pd.DataFrame, session2: pd.DataFrame) -> tuple[list[Path], pd.DataFrame, pd.DataFrame]:
    sealed = master.loc[master["Protocol"].eq("Factorial_3x3_Sealed")]
    s1m = master.loc[master["Protocol"].eq("Matched_Pressure_10PSI")]
    s2m = session2.loc[session2["Protocol"].eq("Matched_Counterbalanced")]
    controls = session2.loc[session2["Protocol"].eq("Baseline_Control")]
    rows = []
    specs = [
        ("Sealed factorial", "Session 1", sealed, "6, 10, 14 PSI nominal", 5),
        ("Matched pressure", "Session 1", s1m, "10 PSI target", 3),
        ("Matched counterbalanced", "Session 2", s2m, "10 PSI target", 3),
        ("Operational baseline checks", "Session 2", controls, "10 PSI target", 1),
    ]
    for protocol, session, frame, nominal, repeats in specs:
        rows.append(
            {
                "Protocol": protocol,
                "Session": session,
                "Temperatures_C": ", ".join(map(str, sorted(frame["Target_Temp_C"].unique()))),
                "Nominal_or_target_pressure": nominal,
                "Achieved_pressure_PSI": f"{frame['Pre_Impact_Press_PSI'].min():.2f}-{frame['Pre_Impact_Press_PSI'].max():.2f}",
                "Number_of_balls": frame["Ball_ID"].nunique(),
                "Repeats_per_cell": repeats,
                "Total_drops": len(frame),
            }
        )
    table1 = pd.DataFrame(rows)
    outputs = write_table_pair(table1, "table1_design_summary")

    components = []
    sealed_copy = sealed.copy()
    sealed_copy["Session"] = "Session 1"
    sealed_copy["Analysis_protocol"] = "Sealed factorial"
    components.append(sealed_copy)
    s1_copy = s1m.copy()
    s1_copy["Session"] = "Session 1"
    s1_copy["Analysis_protocol"] = "Matched pressure"
    components.append(s1_copy)
    s2_copy = s2m.copy()
    s2_copy["Session"] = "Session 2"
    s2_copy["Analysis_protocol"] = "Matched counterbalanced"
    components.append(s2_copy)
    control_copy = controls.copy()
    control_copy["Session"] = "Session 2"
    control_copy["Analysis_protocol"] = "Operational baseline checks"
    components.append(control_copy)
    combined = pd.concat(components, ignore_index=True, sort=False)
    combined["Nominal_Pressure_PSI"] = np.where(
        combined["Analysis_protocol"].eq("Sealed factorial"), combined.get("Target_Press_PSI"), 10
    )
    group_cols = ["Analysis_protocol", "Session", "Target_Temp_C", "Nominal_Pressure_PSI"]
    summary_rows = []
    for key, group in combined.groupby(group_cols, dropna=False, observed=True):
        bm = group.groupby("Ball_ID", observed=True)["Calculated_COR_e"].mean()
        summary_rows.append(
            {
                "Protocol": key[0],
                "Session": key[1],
                "Target_Temp_C": key[2],
                "Nominal_Pressure_PSI": key[3],
                "N_balls": group["Ball_ID"].nunique(),
                "N_drops": len(group),
                "Mean_Surface_Temp_C": group["Surface_Temp_C"].mean() if "Surface_Temp_C" in group and group["Surface_Temp_C"].notna().any() else np.nan,
                "Mean_Pre_Impact_Press_PSI": group["Pre_Impact_Press_PSI"].mean(),
                "Mean_Release_Height_m": group["Release_Height_m"].mean(),
                "Mean_Rebound_Height_m": group["Rebound_Height_m"].mean(),
                "Rebound_Height_SD_across_drops_m": group["Rebound_Height_m"].std(ddof=1),
                "Mean_COR_from_ball_means": bm.mean(),
                "COR_SD_across_drops": group["Calculated_COR_e"].std(ddof=1),
                "COR_SD_across_ball_condition_means": bm.std(ddof=1),
            }
        )
    table2 = pd.DataFrame(summary_rows).sort_values(
        ["Protocol", "Session", "Target_Temp_C", "Nominal_Pressure_PSI"]
    ).reset_index(drop=True)
    outputs += write_table_pair(table2, "table2_condition_summary")

    frames = protocol_frames(master, session2)
    sealed_c = matched_contrasts(frames["Sealed Session 1"])
    s1_c = matched_contrasts(frames["Matched Session 1"])
    s2_c = matched_contrasts(frames["Matched Session 2"])
    table3 = pd.DataFrame(
        {
            "Ball_ID": BALL_ORDER,
            "Session1_matched_delta_e_40_minus_0": s1_c.values,
            "Session2_matched_delta_e_40_minus_0": s2_c.values,
            "Session1_sealed_10PSI_delta_e_40_minus_0": sealed_c.values,
            "Session1_sealed_minus_matched_delta_difference": (sealed_c - s1_c).values,
        }
    )
    outputs += write_table_pair(table3, "table3_ball_level_contrasts")
    return outputs, table2, table3


def write_captions(master: pd.DataFrame, session2: pd.DataFrame) -> Path:
    sealed_n = int(master["Protocol"].eq("Factorial_3x3_Sealed").sum())
    s1m_n = int(master["Protocol"].eq("Matched_Pressure_10PSI").sum())
    s2m_n = int(session2["Protocol"].eq("Matched_Counterbalanced").sum())
    controls_n = int(session2["Protocol"].eq("Baseline_Control").sum())
    text = f"""# Figure captions

**Figure 1. Experimental design and data structure.** (a) Session 1 sealed-ball factorial design crossed three target temperatures (0, 20, and 40 °C), three nominal pressures (6, 10, and 14 PSI at the reference condition), and three balls, with five repeated drops per ball-condition ({sealed_n} drops). (b) Session 1 matched-pressure path used three repeated drops per ball-temperature while adjusting pre-impact gauge pressure to approximately 10 PSI ({s1m_n} drops). (c) Session 2 repeated the matched-pressure experiment with counterbalanced temperature-block orders for the three balls ({s2m_n} experimental drops) and included {controls_n} separate operational baseline checks.

**Figure 2. Session 1 sealed-factorial response.** (a) Recorded height-derived coefficient of restitution (COR) versus target temperature for the three nominal-pressure paths. Small faint points are individual drops, open points are means of repeated drops for each ball-condition, and large connected markers are condition means calculated as the mean of the three ball-condition means. (b) Measured pre-impact gauge pressure for the same observations and summaries. Colors and marker shapes identify nominal pressure at the reference condition; connecting lines join only overall condition means. Each factorial cell contains three balls and five repeated drops per ball ({sealed_n} drops total). The COR axis is truncated to the plotted range (0.70–0.91). The panel describes the sealed experimental path, along which pressure changed with temperature; it does not assign the temperature response to a particular mechanism.

**Figure 2a, standalone COR graph.** Recorded height-derived COR versus target temperature for the Session 1 sealed factorial ({sealed_n} drops; three balls, five repeated drops per ball-temperature-pressure cell). Faint points are individual drops, open markers are ball-condition means, and connected filled markers are the means of the three ball-condition means. Colors and marker shapes identify nominal pressure at the reference condition. The COR axis is truncated to 0.70–0.91.

**Figure 2b, standalone pressure graph.** Measured pre-impact gauge pressure versus target temperature for the same {sealed_n} Session 1 sealed-factorial drops. Faint points are individual drops, open markers are ball-condition means, and connected filled markers are the means of the three ball-condition means. Colors and marker shapes identify nominal pressure at the reference condition. The increase along each line describes the sealed experimental path and does not assign a mechanism to the COR response.

**Figure 3. Matched-pressure replication.** (a) COR versus target temperature for Session 1 ({s1m_n} drops) and Session 2 ({s2m_n} experimental drops; the three operational checks are excluded). Colored thin lines connect repeated-drop means for the same physical ball; thick dark lines are session-wide condition means computed from the three ball means. Dashed and dash-dot lines identify Sessions 1 and 2, respectively. (b) Within-ball 0–40 °C contrasts, $\\Delta e_{{40-0}}=\\bar e_{{40}}-\\bar e_{{0}}$. Circles and diamonds show Sessions 1 and 2; horizontal segments connect the two measurements for the same ball. Larger dark markers show across-ball means. The zero line is a reference. The six plotted session-ball contrasts represent repeated measurements of three balls, not six independent footballs. The COR axis in panel (a) is truncated to 0.775–0.845.

**Figure 4. Comparison of sealed and matched experimental paths.** (a) COR and (b) measured pre-impact gauge pressure versus target temperature for the Session 1 sealed nominal-10-PSI path, Session 1 matched-pressure path, and Session 2 matched-pressure replication. Colored semi-transparent points are repeated-drop means for Ball A, Ball B, and Ball C; connected path lines are overall condition means calculated from the three ball means. Solid, dashed, and dash-dot lines identify sealed Session 1, matched Session 1, and matched Session 2. The sealed protocol allowed pressure to vary naturally with temperature, whereas both matched protocols adjusted pressure before impact. (c) Ball-level 0–40 °C COR changes for each path; small colored points are individual ball contrasts and diamonds are their across-ball means. This is a descriptive comparison between experimental paths, not a decomposition into pressure and material effects. The COR axis in panel (a) is truncated to 0.77–0.89.

**Figure 5. Blinded annotation agreement.** Bland–Altman plots for (a) release height, $h_0$, and (b) rebound height, $h_1$, from 25 videos measured independently by two annotators. Points plot the pairwise mean against Annotator 2 minus Annotator 1 in millimetres. Solid horizontal lines are mean biases; dashed lines are 95% limits of agreement calculated as bias ± 1.96 sample standard deviations. Insets report the sample size, mean bias, mean absolute difference, and limits of agreement.

**Figure S1. Release-height stability.** Release height by Drop ID/run order for Session 1 sealed, Session 1 matched-pressure, and Session 2 observations. Colors identify the three balls; the dashed horizontal reference is 2.500 m. Session 2 operational checks are retained and outlined. The plot is a diagnostic for drift and isolated deviations, not evidence of perfect stability.

**Figure S2. Matched-pressure control.** Individual pre-impact gauge-pressure observations by target temperature and ball for the two matched-pressure sessions. The dashed line is the 10-PSI target reference, not a tolerance boundary. No tolerance band is shown because no prespecified tolerance is encoded in the source files. Drop 161 and the observed Session 1 range are explicitly identified; Session 2 shows only the {s2m_n} experimental drops.

**Figure S3. Exploratory run-order diagnostics.** Within-ball-condition COR residuals versus Drop ID/run order for Session 1 and Session 2. Residuals subtract the repeated-drop mean for the same ball, temperature, and, for the factorial data, nominal-pressure cell. Colors identify balls; marker shapes separate the Session 1 sealed and matched paths. Session 2 operational checks are shown as unconnected outlined squares after centering on their three-check mean because the checks used different balls. These displays are exploratory and do not establish the absence of drift.
"""
    path = PAPER_DIR / "figure_captions.md"
    path.write_text(text, encoding="utf-8")
    return path


def write_analysis_summary(
    master: pd.DataFrame,
    audit: pd.DataFrame,
    session2: pd.DataFrame,
    validation,
    table2: pd.DataFrame,
) -> Path:
    frames = protocol_frames(master, session2)
    contrasts = {name: matched_contrasts(frame) for name, frame in frames.items()}
    sealed_change = contrasts["Sealed Session 1"].mean()
    s1_change = contrasts["Matched Session 1"].mean()
    s2_change = contrasts["Matched Session 2"].mean()
    difference = sealed_change - s1_change
    attenuation = difference / sealed_change * 100
    s1_frame = frames["Matched Session 1"]
    without_161 = s1_frame.loc[~s1_frame["Drop_ID"].eq(161)]
    sensitivity = matched_contrasts(without_161)
    ball_c_original = contrasts["Matched Session 1"].loc["Ball_C"]
    ball_c_excluded = sensitivity.loc["Ball_C"]
    overall_excluded = sensitivity.mean()
    h0 = audit_stats(audit, "h0")
    h1 = audit_stats(audit, "h1")
    range_s1 = s1_frame["Pre_Impact_Press_PSI"].agg(["min", "max"])
    condition_text = table2.to_string(index=False, float_format=lambda x: f"{x:.6f}")
    contrast_lines = []
    for ball in BALL_ORDER:
        contrast_lines.append(
            f"- {BALL_LABEL[ball]}: Session 1 matched {contrasts['Matched Session 1'].loc[ball]:.6f}; "
            f"Session 2 matched {contrasts['Matched Session 2'].loc[ball]:.6f}; "
            f"Session 1 sealed 10-PSI path {contrasts['Sealed Session 1'].loc[ball]:.6f}."
        )
    warning_lines = "\n".join(f"- {x}" for x in validation.warnings) or "- None."
    text = f"""# Analysis summary

## Results generated from the files

- Validated row counts: Session 1 master = {len(master)}; annotation audit = {len(audit)}; Session 2 = {len(session2)}.
- Session 1 contains 135 sealed-factorial and 27 matched-pressure drops. Session 2 contains 27 matched counterbalanced experimental drops and 3 operational baseline checks.
- Session 1 matched-pressure observed pre-impact range: {range_s1['min']:.2f}–{range_s1['max']:.2f} PSI.
- All primary Session 2 temperature-condition means exclude the three operational checks.

### Exact condition summaries

The full machine-readable values are in `tables/table2_condition_summary.csv`. Means of COR are calculated from the three ball-condition means; the two SD columns distinguish variation across drops from variation across ball-condition means.

```text
{condition_text}
```

### Ball-level 0–40 °C COR contrasts

{chr(10).join(contrast_lines)}

Across-ball means were {s1_change:.6f} in Session 1 matched and {s2_change:.6f} in Session 2 matched, a Session 2 minus Session 1 difference of {s2_change-s1_change:+.6f}. The replicated direction was positive for every ball in both sessions.

### Sealed-versus-matched path comparison

The across-ball 0–40 °C change was {sealed_change:.6f} for the Session 1 sealed nominal-10-PSI path and {s1_change:.6f} for the Session 1 matched path. Their descriptive difference was {difference:.6f}; expressed relative to the sealed-path change, this is {attenuation:.2f}%. This percentage compares observed experimental paths and must not be interpreted as the fraction caused by gas pressure or as a material-effect decomposition.

### Drop 161 sensitivity

With all Session 1 matched drops, Ball C's contrast was {ball_c_original:.6f} and the across-ball mean contrast was {s1_change:.6f}. Excluding Drop 161 changes Ball C's contrast to {ball_c_excluded:.6f} and the across-ball mean to {overall_excluded:.6f} (change {overall_excluded-s1_change:+.6f}). The exclusion is a sensitivity check only; the source row remains intact.

### Blinded annotation agreement

- Release height ($h_0$): n = {h0['n']}, bias = {h0['bias_mm']:+.2f} mm, mean absolute difference = {h0['mad_mm']:.2f} mm, 95% limits of agreement = {h0['loa_low_mm']:+.2f} to {h0['loa_high_mm']:+.2f} mm.
- Rebound height ($h_1$): n = {h1['n']}, bias = {h1['bias_mm']:+.2f} mm, mean absolute difference = {h1['mad_mm']:.2f} mm, 95% limits of agreement = {h1['loa_low_mm']:+.2f} to {h1['loa_high_mm']:+.2f} mm.

## Validation warnings

{warning_lines}

Values affected by recorded-COR versus displayed-height discrepancies remain provisional pending source-data correction. Figures and summaries use the recorded `Calculated_COR_e` values and never overwrite them.

## Interpretive statements

Across all three balls, COR increased from 0 to 40 °C in both matched-pressure sessions, and the magnitudes were closely aligned. The sealed nominal-10-PSI path showed a larger descriptive change while its measured pre-impact pressure rose strongly with temperature. These observations compare experimental paths; they do not identify a casing-hysteresis mechanism or partition causal contributions.

## Limitations and statistical units

The study contains three physical balls. Repeated drops are technical/repeated observations, not independent footballs. Overall plotted condition means therefore average the three ball-condition means, and no confidence intervals or p-values treat individual drops as independent units. Across-ball SDs describe variation among only three ball means and are not population-level uncertainty estimates. Run-order displays are exploratory; a visually small trend cannot establish absence of drift. Session 2 controls used different balls and are not treated as a same-ball time series.
"""
    path = PAPER_DIR / "analysis_summary.md"
    path.write_text(text, encoding="utf-8")
    return path


def write_figure_includes() -> Path:
    entries = [
        ("fig1_experimental_design", "experimental-design"),
        ("fig2_sealed_factorial_response", "sealed-factorial"),
        ("fig2a_sealed_factorial_cor", "sealed-factorial-cor"),
        ("fig2b_sealed_factorial_pressure", "sealed-factorial-pressure"),
        ("fig3_matched_pressure_replication", "matched-replication"),
        ("fig4_protocol_path_comparison", "protocol-paths"),
        ("fig5_annotation_agreement", "annotation-agreement"),
    ]
    chunks = []
    for filename, label in entries:
        chunks.append(
            textwrap.dedent(
                rf"""
                % \begin{{figure}}[t]
                %   \centering
                %   \includegraphics[width=\linewidth]{{figures/{filename}.pdf}}
                %   \caption{{Caption placeholder.}}
                %   \label{{fig:{label}}}
                % \end{{figure}}
                """
            ).strip()
        )
    path = FIGURE_DIR / "figure_includes.tex"
    path.write_text("\n\n".join(chunks) + "\n", encoding="utf-8")
    return path


def main() -> int:
    ensure_output_dirs()
    configure_style()
    try:
        master, audit, session2 = load_data()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    validation = validate_frames(master, audit, session2)
    report = write_validation_report(validation)
    if not validation.ok:
        print(f"Critical validation failed; final figures were not generated. See {report}", file=sys.stderr)
        return 1

    outputs: list[Path] = []
    outputs += figure1_design(master, session2)
    outputs += figure2_sealed(master)
    outputs += figure2_sealed_parts(master)
    outputs += figure3_matched(master, session2)
    outputs += figure4_paths(master, session2)
    outputs += figure5_audit(audit)
    outputs += figure_s1_release(master, session2)
    outputs += figure_s2_pressure(master, session2)
    outputs += figure_s3_run_order(master, session2)
    table_outputs, table2, _ = make_tables(master, session2)
    outputs += table_outputs
    outputs.append(write_captions(master, session2))
    outputs.append(write_analysis_summary(master, audit, session2, validation, table2))
    outputs.append(write_figure_includes())

    zero = [str(path) for path in outputs if not path.exists() or path.stat().st_size == 0]
    if zero:
        print("Output generation failed for: " + ", ".join(zero), file=sys.stderr)
        return 1
    print(f"Generated {len(outputs)} non-empty files.")
    for path in outputs:
        print(path.relative_to(Path(__file__).resolve().parents[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
