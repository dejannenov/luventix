"""Tests for the luv-align CLI entry point."""

import importlib
from pathlib import Path

import numpy as np
import pytest

# Import the script module directly
CLI_PATH = Path(__file__).resolve().parent.parent / "src" / "luv-align.py"
spec = importlib.util.spec_from_file_location("luv_align_cli", CLI_PATH)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


class TestParseArgs:
    def test_single_mode_args(self):
        args = cli.parse_args(["--in", "input.tsv", "--out", "output.tsv", "--align-to-id", "s1"])
        assert args.input_file == "input.tsv"
        assert args.output_file == "output.tsv"
        assert args.align_to_id == "s1"
        assert args.full is False

    def test_full_mode_args(self):
        args = cli.parse_args(["--in", "input.tsv", "--full"])
        assert args.input_file == "input.tsv"
        assert args.full is True
        assert args.output_file is None
        assert args.align_to_id is None

    def test_missing_in(self):
        with pytest.raises(SystemExit):
            cli.parse_args(["--out", "out.tsv", "--align-to-id", "s1"])

    def test_missing_out_without_full(self):
        with pytest.raises(SystemExit):
            cli.parse_args(["--in", "in.tsv", "--align-to-id", "s1"])

    def test_missing_align_to_id_without_full(self):
        with pytest.raises(SystemExit):
            cli.parse_args(["--in", "in.tsv", "--out", "out.tsv"])

    def test_full_with_out_rejected(self):
        with pytest.raises(SystemExit):
            cli.parse_args(["--in", "in.tsv", "--full", "--out", "out.tsv"])

    def test_full_with_align_to_id_rejected(self):
        with pytest.raises(SystemExit):
            cli.parse_args(["--in", "in.tsv", "--full", "--align-to-id", "s1"])

    def test_missing_everything(self):
        with pytest.raises(SystemExit):
            cli.parse_args([])


class TestDetectMetadataCols:
    def test_detects_three_metadata_cols(self, sample_tsv):
        result = cli.detect_metadata_cols(sample_tsv)
        assert result == 3

    def test_detects_one_metadata_col(self, tmp_path):
        path = tmp_path / "one_meta.tsv"
        path.write_text("sampleID\t0\t1\t2\ns1\t10\t20\t30\n")
        assert cli.detect_metadata_cols(str(path)) == 1

    def test_raises_on_no_numeric_cols(self, tmp_path):
        path = tmp_path / "no_numeric.tsv"
        path.write_text("sampleID\tcondition\tstatus\ns1\tctrl\tok\n")
        with pytest.raises(ValueError, match="No numeric scan columns"):
            cli.detect_metadata_cols(str(path))


class TestMainSingleMode:
    def test_full_pipeline(self, sample_tsv, tmp_path):
        output = str(tmp_path / "aligned_out.tsv")
        cli.main(["--in", sample_tsv, "--out", output, "--align-to-id", "ref-001"])

        from luv_align.io import load_sample_matrix

        df, _, features = load_sample_matrix(output, metadata_cols=1)
        assert len(df) == 3
        assert df.iloc[0]["sampleID"] == "ref-001"
        assert features.shape[1] == 100

    def test_reference_signal_unchanged(self, sample_tsv, tmp_path):
        output = str(tmp_path / "aligned_out.tsv")
        cli.main(["--in", sample_tsv, "--out", output, "--align-to-id", "ref-001"])

        from luv_align.io import load_sample_matrix

        _orig_df, _, orig_features = load_sample_matrix(sample_tsv, metadata_cols=3)
        _aligned_df, _, aligned_features = load_sample_matrix(output, metadata_cols=1)

        orig_ref = orig_features.iloc[0].values.astype(float)
        aligned_ref = aligned_features.iloc[0].values.astype(float)
        np.testing.assert_allclose(aligned_ref, orig_ref, atol=1e-10)

    def test_invalid_reference_id(self, sample_tsv, tmp_path):
        output = str(tmp_path / "aligned_out.tsv")
        with pytest.raises(SystemExit):
            cli.main(["--in", sample_tsv, "--out", output, "--align-to-id", "nonexistent"])

    def test_different_reference(self, sample_tsv, tmp_path):
        output = str(tmp_path / "aligned_out.tsv")
        cli.main(["--in", sample_tsv, "--out", output, "--align-to-id", "tgt-001"])

        from luv_align.io import load_sample_matrix

        df, _, _ = load_sample_matrix(output, metadata_cols=1)
        assert df.iloc[0]["sampleID"] == "tgt-001"
        assert len(df) == 3


class TestMainFullMode:
    def test_creates_one_file_per_sample(self, sample_tsv, tmp_path):
        # Copy input to tmp_path so output lands there
        import shutil

        input_copy = str(tmp_path / "data.tsv")
        shutil.copy(sample_tsv, input_copy)

        cli.main(["--in", input_copy, "--full"])

        assert (tmp_path / "ref-001-aligned.tsv").exists()
        assert (tmp_path / "tgt-001-aligned.tsv").exists()
        assert (tmp_path / "tgt-002-aligned.tsv").exists()

    def test_each_file_has_correct_reference(self, sample_tsv, tmp_path):
        import shutil

        from luv_align.io import load_sample_matrix

        input_copy = str(tmp_path / "data.tsv")
        shutil.copy(sample_tsv, input_copy)

        cli.main(["--in", input_copy, "--full"])

        # Each file should have its reference as the first row
        for ref_id in ["ref-001", "tgt-001", "tgt-002"]:
            df, _, _ = load_sample_matrix(str(tmp_path / f"{ref_id}-aligned.tsv"), metadata_cols=1)
            assert df.iloc[0]["sampleID"] == ref_id
            assert len(df) == 3

    def test_reference_row_unchanged_in_each_file(self, sample_tsv, tmp_path):
        import shutil

        from luv_align.io import load_sample_matrix

        input_copy = str(tmp_path / "data.tsv")
        shutil.copy(sample_tsv, input_copy)

        cli.main(["--in", input_copy, "--full"])

        # Load original signals
        _orig_df, _, orig_features = load_sample_matrix(sample_tsv, metadata_cols=3)

        for i, ref_id in enumerate(["ref-001", "tgt-001", "tgt-002"]):
            _aligned_df, _, aligned_features = load_sample_matrix(
                str(tmp_path / f"{ref_id}-aligned.tsv"), metadata_cols=1
            )
            orig_signal = orig_features.iloc[i].values.astype(float)
            aligned_ref = aligned_features.iloc[0].values.astype(float)
            np.testing.assert_allclose(aligned_ref, orig_signal, atol=1e-10)
