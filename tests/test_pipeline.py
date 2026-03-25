"""Tests for luv_align.pipeline module."""

import lzma

import numpy as np

from luv_align.pipeline import align_and_compress, align_to_reference, get_worker_count


class TestAlignToReference:
    def test_exports_file(self, ref_signal, tgt_signal, scan_axis, tmp_path):
        signals = {"ref": ref_signal, "tgt": tgt_signal}
        output = str(tmp_path / "out.tsv")
        align_to_reference(signals, "ref", ["ref", "tgt"], scan_axis, output)
        assert (tmp_path / "out.tsv").exists()


class TestAlignAndCompress:
    def test_produces_xz_and_removes_tsv(self, ref_signal, tgt_signal, scan_axis, tmp_path):
        signals = {"ref": ref_signal, "tgt": tgt_signal}
        result = align_and_compress(signals, "ref", ["ref", "tgt"], scan_axis, str(tmp_path), 1, 1)

        assert (tmp_path / "ref-aligned.tsv.xz").exists()
        assert not (tmp_path / "ref-aligned.tsv").exists()
        assert "[1 of 1]" in result

    def test_xz_contains_valid_tsv(self, ref_signal, tgt_signal, scan_axis, tmp_path):
        signals = {"ref": ref_signal, "tgt": tgt_signal}
        align_and_compress(signals, "ref", ["ref", "tgt"], scan_axis, str(tmp_path), 1, 1)

        xz_path = tmp_path / "ref-aligned.tsv.xz"
        with lzma.open(xz_path, "rb") as f:
            content = f.read().decode()
        assert "sampleID" in content
        assert "ref" in content


class TestGetWorkerCount:
    def test_returns_at_least_one(self):
        assert get_worker_count() >= 1

    def test_returns_int(self):
        assert isinstance(get_worker_count(), int)

    def test_full_dtw_caps_at_two(self):
        assert get_worker_count(use_full_dtw=True) <= 2
