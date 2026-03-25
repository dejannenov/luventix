"""Tests for data I/O functions."""

import numpy as np
import pytest

from luv_align.io import (
    _format_size,
    export_aligned_matrix,
    extract_multiple_signals,
    extract_signal,
    load_peaks_file,
    load_sample_matrix,
)


class TestFormatSize:
    def test_bytes(self):
        assert _format_size(512) == "512.0 B"

    def test_megabytes(self):
        assert _format_size(1024 * 1024 * 5) == "5.0 MB"

    def test_terabytes(self):
        assert _format_size(1024**4 * 2) == "2.0 TB"


class TestLoadSampleMatrix:
    def test_loads_tsv_correctly(self, sample_tsv):
        df, scan_axis, features_df = load_sample_matrix(sample_tsv, metadata_cols=3)
        assert len(df) == 3
        assert len(scan_axis) == 100
        assert features_df.shape == (3, 100)
        assert features_df.columns.dtype == np.int64

    def test_scan_axis_is_integer(self, sample_tsv):
        _, scan_axis, _ = load_sample_matrix(sample_tsv, metadata_cols=3)
        assert scan_axis[0] == 0
        assert scan_axis[-1] == 99


class TestExtractSignal:
    def test_extracts_valid_sample(self, sample_tsv):
        df, _, features_df = load_sample_matrix(sample_tsv, metadata_cols=3)
        signal = extract_signal(df, features_df, "ref-001")
        assert isinstance(signal, np.ndarray)
        assert signal.ndim == 1
        assert signal.dtype == float
        assert len(signal) == 100

    def test_raises_on_missing_sample(self, sample_tsv):
        df, _, features_df = load_sample_matrix(sample_tsv, metadata_cols=3)
        with pytest.raises(ValueError, match="not found"):
            extract_signal(df, features_df, "nonexistent")

    def test_signal_has_peaks(self, sample_tsv):
        df, _, features_df = load_sample_matrix(sample_tsv, metadata_cols=3)
        signal = extract_signal(df, features_df, "ref-001")
        assert np.max(signal) > 0
        # Peak near scan 30
        assert signal[30] > signal[0]


class TestExtractMultipleSignals:
    def test_extracts_all_samples(self, sample_tsv):
        df, _, features_df = load_sample_matrix(sample_tsv, metadata_cols=3)
        signals = extract_multiple_signals(df, features_df, ["ref-001", "tgt-001"])
        assert len(signals) == 2
        assert "ref-001" in signals
        assert "tgt-001" in signals

    def test_raises_on_missing_sample(self, sample_tsv):
        df, _, features_df = load_sample_matrix(sample_tsv, metadata_cols=3)
        with pytest.raises(ValueError, match="not found"):
            extract_multiple_signals(df, features_df, ["ref-001", "nonexistent"])


class TestExportAlignedMatrix:
    def test_raises_on_empty_sample_ids(self, tmp_path, scan_axis):
        with pytest.raises(ValueError, match="sample_ids must be non-empty"):
            export_aligned_matrix({}, [], scan_axis, str(tmp_path / "out.tsv"))

    def test_raises_when_first_id_missing(self, tmp_path, ref_signal, scan_axis):
        with pytest.raises(ValueError, match="sample_ids must be non-empty"):
            export_aligned_matrix(
                {"other": ref_signal}, ["missing"], scan_axis, str(tmp_path / "out.tsv")
            )

    def test_exports_tsv(self, tmp_path, ref_signal, tgt_signal, scan_axis):
        signals = {"ref-001": ref_signal, "tgt-001": tgt_signal}
        output = str(tmp_path / "aligned.tsv")
        export_aligned_matrix(signals, ["ref-001", "tgt-001"], scan_axis, output)

        reloaded_df, _, reloaded_features = load_sample_matrix(output, metadata_cols=1)
        assert len(reloaded_df) == 2
        assert reloaded_df.iloc[0]["sampleID"] == "ref-001"
        assert reloaded_features.shape[1] == 100


class TestLoadPeaksFile:
    def test_parses_peaks_file(self, peaks_file):
        peaks = load_peaks_file(peaks_file)
        assert peaks["ref-001"] == (30, 70)
        assert peaks["tgt-001"] == (33, 73)
        assert peaks["tgt-002"] == (28, 68)

    def test_handles_empty_lines(self, tmp_path):
        path = tmp_path / "peaks.txt"
        path.write_text("ref-001 - 30 70\n\n\ntgt-001 - 33 73\n")
        peaks = load_peaks_file(str(path))
        assert len(peaks) == 2
