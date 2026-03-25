"""Tests for plotting functions (mocked plt.show)."""

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from luv_align.plotting import (
    _on_hover,
    plot_aligned_signals,
    plot_signal_with_peaks,
    plot_with_tooltips,
)

# Use non-interactive backend for testing
matplotlib.use("Agg")


class TestPlotSignalWithPeaks:
    def test_returns_figure(self, ref_signal, scan_axis):
        peak_indices = np.array([30, 70])
        fig = plot_signal_with_peaks(ref_signal, scan_axis, "test-sample", peak_indices)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_figure_has_axes(self, ref_signal, scan_axis):
        peak_indices = np.array([30, 70])
        fig = plot_signal_with_peaks(ref_signal, scan_axis, "test-sample", peak_indices)
        assert len(fig.axes) == 1
        ax = fig.axes[0]
        assert ax.get_xlabel() == "Scan Number"
        assert ax.get_ylabel() == "Intensity"
        plt.close(fig)

    def test_empty_peaks(self, ref_signal, scan_axis):
        fig = plot_signal_with_peaks(ref_signal, scan_axis, "test-sample", np.array([], dtype=int))
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestPlotAlignedSignals:
    def test_returns_figure(self, ref_signal, tgt_signal, scan_axis):
        signals = {"ref": ref_signal, "tgt": tgt_signal}
        fig = plot_aligned_signals(signals, ["ref", "tgt"], scan_axis)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_custom_title(self, ref_signal, scan_axis):
        signals = {"ref": ref_signal}
        fig = plot_aligned_signals(signals, ["ref"], scan_axis, title="Custom Title")
        assert fig.axes[0].get_title() == "Custom Title"
        plt.close(fig)

    def test_missing_sample_skipped(self, ref_signal, scan_axis):
        signals = {"ref": ref_signal}
        fig = plot_aligned_signals(signals, ["ref", "missing"], scan_axis)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


class TestPlotWithTooltips:
    def test_returns_figure(self):
        df = pd.DataFrame({"sampleID": ["s1", "s2"], "0": [1.0, 2.0], "1": [3.0, 4.0]})
        features_df = df.iloc[:, 1:].copy()
        features_df.columns = features_df.columns.astype(int)
        fig = plot_with_tooltips(df, features_df)
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_lines_have_gids(self):
        df = pd.DataFrame({"sampleID": ["s1"], "0": [1.0], "1": [2.0]})
        features_df = df.iloc[:, 1:].copy()
        features_df.columns = features_df.columns.astype(int)
        fig = plot_with_tooltips(df, features_df)
        lines = fig.axes[0].get_lines()
        assert lines[0].get_gid() == "s1"
        plt.close(fig)

    def test_hover_callback(self):
        from unittest.mock import MagicMock

        sel = MagicMock()
        sel.target = (42.0, 123.45)
        sel.artist.get_gid.return_value = "sample-1"
        bbox_patch = MagicMock()
        sel.annotation.get_bbox_patch.return_value = bbox_patch

        _on_hover(sel)

        sel.annotation.set_text.assert_called_once_with(
            "sample-1\nScan: 42\nIntensity: 123.45"
        )
        bbox_patch.set.assert_called_once_with(alpha=0.9)
