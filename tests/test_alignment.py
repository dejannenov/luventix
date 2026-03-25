"""Tests for alignment functions."""

import numpy as np

from luv_align.alignment import (
    _deduplicate_path,
    align_all_samples,
    align_with_dtw,
    apply_intensity_threshold,
    variable_shift_signal,
)


class TestVariableShiftSignal:
    def test_no_shift_when_peaks_match(self, ref_signal):
        # When ref and target peaks are identical, signal should be unchanged
        result = variable_shift_signal(ref_signal, ref_peaks=[30, 70], tgt_peaks=[30, 70])
        np.testing.assert_allclose(result, ref_signal, atol=1e-10)

    def test_shift_moves_peaks(self, tgt_signal):
        # Target has peaks at 33, 73; shift to ref peaks at 30, 70
        result = variable_shift_signal(tgt_signal, ref_peaks=[30, 70], tgt_peaks=[33, 73])
        # After shift, peak should be closer to 30
        peak_region = result[28:33]
        assert np.argmax(peak_region) <= 2  # peak moved left

    def test_output_shape_matches_input(self, ref_signal):
        result = variable_shift_signal(ref_signal, ref_peaks=[30, 70], tgt_peaks=[33, 73])
        assert result.shape == ref_signal.shape

    def test_edges_filled_with_zero(self):
        # Shift that pushes signal out of bounds should fill with 0 or NaN
        signal = np.ones(50)
        result = variable_shift_signal(signal, ref_peaks=[10, 40], tgt_peaks=[40, 45])
        # Large shift pushes early indices to negative source positions → fill_value=0
        assert result[0] == 0.0


class TestDeduplicatePath:
    def test_no_duplicates_unchanged(self):
        x = np.array([0, 1, 2, 3])
        y = np.array([10.0, 20.0, 30.0, 40.0])
        ux, uy = _deduplicate_path(x, y)
        np.testing.assert_array_equal(ux, x)
        np.testing.assert_array_equal(uy, y)

    def test_duplicates_averaged(self):
        x = np.array([0, 1, 1, 2])
        y = np.array([10.0, 20.0, 30.0, 40.0])
        ux, uy = _deduplicate_path(x, y)
        np.testing.assert_array_equal(ux, [0, 1, 2])
        np.testing.assert_array_equal(uy, [10.0, 25.0, 40.0])

    def test_all_same_index(self):
        x = np.array([5, 5, 5])
        y = np.array([10.0, 20.0, 30.0])
        ux, uy = _deduplicate_path(x, y)
        np.testing.assert_array_equal(ux, [5])
        np.testing.assert_allclose(uy, [20.0])


class TestAlignWithDtw:
    def test_identical_signals_unchanged(self, ref_signal):
        result = align_with_dtw(ref_signal, ref_signal)
        # DTW of identical signals should be very close to original
        np.testing.assert_allclose(result, ref_signal, atol=1.0)

    def test_output_length_matches_reference(self, ref_signal, tgt_signal):
        result = align_with_dtw(ref_signal, tgt_signal)
        assert len(result) == len(ref_signal)

    def test_aligned_signal_is_float(self, ref_signal, tgt_signal):
        result = align_with_dtw(ref_signal, tgt_signal)
        assert result.dtype == float


class TestApplyIntensityThreshold:
    def test_zeros_below_threshold(self):
        signal = np.array([0.5, 1.5, 2.5, 0.1, 3.0])
        result = apply_intensity_threshold(signal, threshold=1.0)
        expected = np.array([0.0, 1.5, 2.5, 0.0, 3.0])
        np.testing.assert_array_equal(result, expected)

    def test_zero_threshold_passes_all(self):
        signal = np.array([0.0, 1.0, 2.0])
        result = apply_intensity_threshold(signal, threshold=0)
        np.testing.assert_array_equal(result, signal)

    def test_high_threshold_zeros_all(self):
        signal = np.array([1.0, 2.0, 3.0])
        result = apply_intensity_threshold(signal, threshold=100)
        np.testing.assert_array_equal(result, np.zeros(3))


class TestAlignAllSamples:
    def test_aligns_multiple_samples(self, ref_signal, tgt_signal):
        signals = {"ref-001": ref_signal, "tgt-001": tgt_signal}
        result = align_all_samples(
            ref_signal=ref_signal,
            sample_signals=signals,
            ref_id="ref-001",
            target_anchor_peaks={"tgt-001": (33, 73)},
            ref_peaks=[30, 70],
            intensity_threshold=0,
        )
        assert "ref-001" in result
        assert "tgt-001" in result
        assert len(result["tgt-001"]) == len(ref_signal)

    def test_reference_unchanged(self, ref_signal, tgt_signal):
        signals = {"ref-001": ref_signal, "tgt-001": tgt_signal}
        result = align_all_samples(
            ref_signal=ref_signal,
            sample_signals=signals,
            ref_id="ref-001",
            target_anchor_peaks={"tgt-001": (33, 73)},
            ref_peaks=[30, 70],
        )
        # Reference should only be thresholded (threshold=0 so unchanged)
        np.testing.assert_array_equal(result["ref-001"], ref_signal)

    def test_sample_without_anchor_peaks_still_aligned(self, ref_signal, tgt_signal):
        signals = {"ref-001": ref_signal, "tgt-001": tgt_signal}
        result = align_all_samples(
            ref_signal=ref_signal,
            sample_signals=signals,
            ref_id="ref-001",
            target_anchor_peaks={},  # no anchor peaks
            ref_peaks=[30, 70],
        )
        assert "tgt-001" in result
        assert len(result["tgt-001"]) == len(ref_signal)

    def test_empty_signal(self, ref_signal):
        zero_signal = np.zeros_like(ref_signal)
        signals = {"ref-001": ref_signal, "zero": zero_signal}
        result = align_all_samples(
            ref_signal=ref_signal,
            sample_signals=signals,
            ref_id="ref-001",
            target_anchor_peaks={},
            ref_peaks=[30, 70],
        )
        # Zero signal aligned should still be all zeros
        np.testing.assert_array_equal(result["zero"], np.zeros(len(ref_signal)))
