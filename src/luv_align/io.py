"""Data I/O for TSV sample matrices and peaks files."""

import numpy as np
import pandas as pd


def load_sample_matrix(
    filepath: str, metadata_cols: int
) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """Load a TSV sample matrix and split into metadata + features.

    Returns:
        Tuple of (full_df, scan_axis, features_df) where scan_axis is the
        integer scan column indices and features_df has int column names.
    """
    df = pd.read_csv(filepath, sep="\t", low_memory=False)
    features_df = df.iloc[:, metadata_cols:].copy()
    features_df.columns = features_df.columns.astype(str).str.strip().astype(int)
    scan_axis = features_df.columns.values
    return df, scan_axis, features_df


def extract_signal(df: pd.DataFrame, features_df: pd.DataFrame, sample_id: str) -> np.ndarray:
    """Extract a single sample's intensity signal as a 1D float array.

    Raises:
        ValueError: If sample_id is not found in the DataFrame.
    """
    row = df[df["sampleID"] == sample_id]
    if row.empty:
        raise ValueError(f"Sample '{sample_id}' not found")
    signal = pd.to_numeric(features_df.loc[row.index[0]], errors="coerce").fillna(0)
    return np.ravel(signal.values).astype(float)


def extract_multiple_signals(
    df: pd.DataFrame, features_df: pd.DataFrame, sample_ids: list[str]
) -> dict[str, np.ndarray]:
    """Extract signals for multiple samples."""
    return {sid: extract_signal(df, features_df, sid) for sid in sample_ids}


def export_aligned_matrix(
    signals: dict[str, np.ndarray],
    sample_ids: list[str],
    scan_axis: np.ndarray,
    output_file: str,
) -> None:
    """Export aligned signals to a TSV file with sampleID + scan columns."""
    if not sample_ids or sample_ids[0] not in signals:
        raise ValueError("sample_ids must be non-empty and first ID must be present in signals")
    rows = []
    for sample_id in sample_ids:
        if sample_id in signals:
            rows.append([sample_id, *list(signals[sample_id])])
    output_df = pd.DataFrame(rows)
    output_df.columns = ["sampleID", *list(scan_axis[: len(signals[sample_ids[0]])])]
    output_df.to_csv(output_file, sep="\t", index=False)


def load_peaks_file(filepath: str) -> dict[str, tuple[int, int]]:
    """Parse a Peaks.txt file into a dict of sample_id -> (peak1_scan, peak2_scan).

    Format per line: `sampleID - peak1_scan peak2_scan`
    """
    peaks = {}
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sample_id, _, peak_str = line.partition(" - ")
            parts = peak_str.strip().split()
            if len(parts) >= 2:
                peaks[sample_id.strip()] = (int(parts[0]), int(parts[1]))
    return peaks
