"""Tests for peak detection."""

import numpy as np

from luv_align.peaks import detect_peaks


class TestDetectPeaks:
    def test_detects_known_peaks(self, ref_signal, scan_axis):
        # Use lower threshold to catch both peaks (second peak is 80% of first)
        peak_indices, peak_scans = detect_peaks(
            ref_signal, scan_axis, height_fraction=0.05, distance=10
        )
        assert len(peak_indices) >= 1
        assert any(abs(s - 30) <= 2 for s in peak_scans)

    def test_returns_numpy_arrays(self, ref_signal, scan_axis):
        peak_indices, peak_scans = detect_peaks(ref_signal, scan_axis)
        assert isinstance(peak_indices, np.ndarray)
        assert isinstance(peak_scans, np.ndarray)

    def test_height_fraction_filters_small_peaks(self, scan_axis):
        # Signal with one big peak and one tiny peak
        signal = np.zeros(100)
        signal += 100 * np.exp(-0.5 * ((np.arange(100) - 50) / 3) ** 2)
        signal += 2 * np.exp(-0.5 * ((np.arange(100) - 20) / 3) ** 2)

        # High threshold should only find the big peak
        peak_indices, _ = detect_peaks(signal, scan_axis, height_fraction=0.5)
        assert len(peak_indices) == 1

    def test_distance_parameter(self, scan_axis):
        # Two peaks very close together
        signal = np.zeros(100)
        signal += 100 * np.exp(-0.5 * ((np.arange(100) - 50) / 1) ** 2)
        signal += 100 * np.exp(-0.5 * ((np.arange(100) - 53) / 1) ** 2)

        # Large distance should merge them
        peak_indices, _ = detect_peaks(signal, scan_axis, height_fraction=0.01, distance=10)
        assert len(peak_indices) == 1

    def test_flat_signal_no_peaks(self, scan_axis):
        signal = np.ones(100) * 5
        peak_indices, _ = detect_peaks(signal, scan_axis)
        assert len(peak_indices) == 0
