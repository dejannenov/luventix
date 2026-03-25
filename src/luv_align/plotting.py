"""Visualization functions for chromatographic signals."""

import matplotlib.pyplot as plt
import mplcursors
import numpy as np


def plot_signal_with_peaks(
    signal: np.ndarray,
    scan_axis: np.ndarray,
    sample_id: str,
    peak_indices: np.ndarray,
    figsize: tuple[int, int] = (16, 6),
) -> plt.Figure:
    """Plot a single signal with annotated detected peaks."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(scan_axis, signal, label=sample_id, lw=1)
    ax.plot(scan_axis[peak_indices], signal[peak_indices], "rx", label="Detected Peaks")

    for p in peak_indices:
        ax.annotate(
            str(scan_axis[p]),
            (scan_axis[p], signal[p]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=8,
        )

    ax.set_xlabel("Scan Number")
    ax.set_ylabel("Intensity")
    ax.set_title(f"Reference Sample: {sample_id}")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_aligned_signals(
    signals: dict[str, np.ndarray],
    sample_ids: list[str],
    scan_axis: np.ndarray,
    title: str = "FastDTW Aligned Samples",
    figsize: tuple[int, int] = (14, 7),
) -> plt.Figure:
    """Plot multiple aligned signals overlaid."""
    fig, ax = plt.subplots(figsize=figsize)
    for sample_id in sample_ids:
        if sample_id in signals:
            ax.plot(scan_axis[: len(signals[sample_id])], signals[sample_id], label=sample_id)
    ax.set_xlabel("Scan Number")
    ax.set_ylabel("Intensity")
    ax.set_title(title)
    ax.legend()
    ax.grid(True)
    fig.tight_layout()
    return fig


def plot_with_tooltips(
    df,
    features_df,
    figsize: tuple[int, int] = (14, 7),
) -> plt.Figure:
    """Plot all samples from a DataFrame with interactive mplcursors hover tooltips."""
    fig, ax = plt.subplots(figsize=figsize)
    lines = []

    for idx, row in df.iterrows():
        sample_id = row["sampleID"]
        intensities = features_df.loc[idx].astype(float)
        (line,) = ax.plot(features_df.columns, intensities, label=sample_id, linewidth=1)
        line.set_gid(sample_id)
        lines.append(line)

    ax.set_xlabel("Scan Index")
    ax.set_ylabel("Intensity")
    ax.set_title("Plot Samples")
    ax.grid(True)
    fig.tight_layout()

    cursor = mplcursors.cursor(lines, hover=True)
    cursor.connect("add", _on_hover)

    return fig


def _on_hover(sel):
    """Handle mplcursors hover event — show sample name, scan, and intensity."""
    x, y = sel.target
    sample_name = sel.artist.get_gid()
    sel.annotation.set_text(f"{sample_name}\nScan: {int(x)}\nIntensity: {y:.2f}")
    sel.annotation.get_bbox_patch().set(alpha=0.9)
