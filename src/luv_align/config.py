"""Configuration dataclasses for pipeline stages."""

from dataclasses import dataclass, field


@dataclass
class IdentPeaksConfig:
    """Configuration for peak identification stage."""

    input_file: str = "SIBO_Test_Set.tsv"
    metadata_cols: int = 3
    sample_id_to_plot: str = "sibo-uk-6"
    peak_height_fraction: float = 0.08
    peak_distance: int = 50


@dataclass
class AlignmentConfig:
    """Configuration for alignment stage."""

    input_file: str = "SIBO_Test_Set.tsv"
    output_file: str = "Aligned_SIBO_Test_Set.tsv"
    metadata_cols: int = 3
    sample_ids_to_plot: list[str] = field(
        default_factory=lambda: ["sibo-uk-6", "uk-0001-00360", "uk-0001-00834"]
    )
    intensity_threshold: float = 0
    ref_peak1_scan: int = 9949
    ref_peak2_scan: int = 32429
    target_anchor_peaks: dict[str, tuple[int, int]] = field(
        default_factory=lambda: {
            "uk-0001-00360": (10168, 32856),
            "uk-0001-00834": (10040, 32603),
        }
    )


@dataclass
class PlotConfig:
    """Configuration for plotting stage."""

    input_file: str = "Aligned_SIBO_Test_Set.tsv"
    metadata_cols: int = 1
