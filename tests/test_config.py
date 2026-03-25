"""Tests for configuration dataclasses."""

from luv_align.config import AlignmentConfig, IdentPeaksConfig, PlotConfig


class TestIdentPeaksConfig:
    def test_defaults(self):
        config = IdentPeaksConfig()
        assert config.input_file == "SIBO_Test_Set.tsv"
        assert config.metadata_cols == 3
        assert config.sample_id_to_plot == "sibo-uk-6"
        assert config.peak_height_fraction == 0.08
        assert config.peak_distance == 50

    def test_custom_values(self):
        config = IdentPeaksConfig(input_file="custom.tsv", sample_id_to_plot="my-sample")
        assert config.input_file == "custom.tsv"
        assert config.sample_id_to_plot == "my-sample"


class TestAlignmentConfig:
    def test_defaults(self):
        config = AlignmentConfig()
        assert config.input_file == "SIBO_Test_Set.tsv"
        assert config.output_file == "Aligned_SIBO_Test_Set.tsv"
        assert config.metadata_cols == 3
        assert len(config.sample_ids_to_plot) == 3
        assert config.intensity_threshold == 0
        assert config.ref_peak1_scan == 9949
        assert config.ref_peak2_scan == 32429
        assert "uk-0001-00360" in config.target_anchor_peaks

    def test_mutable_defaults_are_independent(self):
        c1 = AlignmentConfig()
        c2 = AlignmentConfig()
        c1.sample_ids_to_plot.append("extra")
        assert "extra" not in c2.sample_ids_to_plot

    def test_custom_values(self):
        config = AlignmentConfig(
            sample_ids_to_plot=["a", "b"],
            target_anchor_peaks={"b": (10, 20)},
        )
        assert config.sample_ids_to_plot == ["a", "b"]
        assert config.target_anchor_peaks == {"b": (10, 20)}


class TestPlotConfig:
    def test_defaults(self):
        config = PlotConfig()
        assert config.input_file == "Aligned_SIBO_Test_Set.tsv"
        assert config.metadata_cols == 1

    def test_custom_values(self):
        config = PlotConfig(input_file="custom.tsv", metadata_cols=3)
        assert config.input_file == "custom.tsv"
        assert config.metadata_cols == 3
