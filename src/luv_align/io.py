"""Data I/O for TSV sample matrices and peaks files."""

import sys
import time

import numpy as np
import pandas as pd


def _format_size(nbytes: int) -> str:
    """Format byte count as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def _log(msg: str) -> None:
    """Print a timestamped status message."""
    print(msg, flush=True)


def load_sample_matrix(
    filepath: str, metadata_cols: int
) -> tuple[pd.DataFrame, np.ndarray, pd.DataFrame]:
    """Load a TSV sample matrix and split into metadata + features.

    Returns:
        Tuple of (full_df, scan_axis, features_df) where scan_axis is the
        integer scan column indices and features_df has int column names.
    """
    t0 = time.monotonic()

    # Read header to determine column types
    header = pd.read_csv(filepath, sep="\t", nrows=0)
    all_cols = list(header.columns)
    meta_names = all_cols[:metadata_cols]
    feature_names = all_cols[metadata_cols:]

    # Build dtype map: metadata as string, features as float32
    dtypes = {col: str for col in meta_names}
    dtypes.update({col: np.float64 for col in feature_names})

    _log(f"Loading {filepath} ({len(feature_names)} scan columns)...")
    df = pd.read_csv(filepath, sep="\t", dtype=dtypes, engine="c", na_values=["", "NA", "NaN"])
    elapsed = time.monotonic() - t0

    mem_bytes = df.memory_usage(deep=True).sum()
    _log(
        f"Loaded {len(df)} samples x {len(feature_names)} scans "
        f"in {elapsed:.1f}s ({_format_size(mem_bytes)} in memory)"
    )

    features_df = df.iloc[:, metadata_cols:]
    features_df = features_df.fillna(0)
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
    return np.ascontiguousarray(features_df.loc[row.index[0]].values, dtype=np.float64)


def extract_multiple_signals(
    df: pd.DataFrame, features_df: pd.DataFrame, sample_ids: list[str]
) -> dict[str, np.ndarray]:
    """Extract signals for multiple samples as contiguous float32 arrays."""
    t0 = time.monotonic()
    _log(f"Extracting {len(sample_ids)} sample signals...")

    # Build sampleID → row index lookup once
    id_to_idx = {}
    for idx, sid in zip(df.index, df["sampleID"]):
        id_to_idx[sid] = idx

    # Bulk-convert features to float32 numpy matrix
    matrix = np.ascontiguousarray(features_df.values, dtype=np.float64)

    signals = {}
    for sid in sample_ids:
        if sid not in id_to_idx:
            raise ValueError(f"Sample '{sid}' not found")
        row_idx = id_to_idx[sid]
        # Map DataFrame index to positional index
        pos = features_df.index.get_loc(row_idx)
        signals[sid] = np.array(matrix[pos], copy=True)

    elapsed = time.monotonic() - t0
    mem_bytes = sum(s.nbytes for s in signals.values())
    _log(f"Extracted {len(signals)} signals in {elapsed:.1f}s ({_format_size(mem_bytes)})")
    return signals


def export_aligned_matrix(
    signals: dict[str, np.ndarray],
    sample_ids: list[str],
    scan_axis: np.ndarray,
    output_file: str,
) -> None:
    """Export aligned signals to a TSV file with sampleID + scan columns."""
    if not sample_ids or sample_ids[0] not in signals:
        raise ValueError("sample_ids must be non-empty and first ID must be present in signals")

    # Build numpy matrix for fast export
    present_ids = [sid for sid in sample_ids if sid in signals]
    n_scans = len(signals[present_ids[0]])
    matrix = np.empty((len(present_ids), n_scans), dtype=np.float64)
    for i, sid in enumerate(present_ids):
        matrix[i] = signals[sid][:n_scans]

    # Write header
    scan_cols = scan_axis[:n_scans]
    with open(output_file, "w") as f:
        f.write("sampleID\t")
        f.write("\t".join(str(c) for c in scan_cols))
        f.write("\n")
        for i, sid in enumerate(present_ids):
            f.write(sid)
            f.write("\t")
            f.write("\t".join(f"{v:.15g}" for v in matrix[i]))
            f.write("\n")


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
