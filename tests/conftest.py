"""Shared test fixtures with small synthetic data."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    """Create a small synthetic sample DataFrame with 3 samples x 100 scans."""
    n_scans = 100
    scan_cols = list(range(n_scans))

    # Reference signal: two gaussian peaks at scan 30 and 70
    ref = np.zeros(n_scans)
    ref += 100 * np.exp(-0.5 * ((np.arange(n_scans) - 30) / 3) ** 2)
    ref += 80 * np.exp(-0.5 * ((np.arange(n_scans) - 70) / 3) ** 2)

    # Target 1: peaks shifted to 33 and 73
    tgt1 = np.zeros(n_scans)
    tgt1 += 100 * np.exp(-0.5 * ((np.arange(n_scans) - 33) / 3) ** 2)
    tgt1 += 80 * np.exp(-0.5 * ((np.arange(n_scans) - 73) / 3) ** 2)

    # Target 2: peaks shifted to 28 and 68
    tgt2 = np.zeros(n_scans)
    tgt2 += 100 * np.exp(-0.5 * ((np.arange(n_scans) - 28) / 3) ** 2)
    tgt2 += 80 * np.exp(-0.5 * ((np.arange(n_scans) - 68) / 3) ** 2)

    data = {
        "sampleID": ["ref-001", "tgt-001", "tgt-002"],
        "condition": ["ctrl", "test", "test"],
        "diseasePresentFlag": [0, 1, 1],
    }
    for i, col in enumerate(scan_cols):
        data[str(col)] = [ref[i], tgt1[i], tgt2[i]]

    return pd.DataFrame(data)


@pytest.fixture
def sample_tsv(tmp_path, sample_df):
    """Write the sample DataFrame to a TSV file and return the path."""
    path = tmp_path / "test_data.tsv"
    sample_df.to_csv(path, sep="\t", index=False)
    return str(path)


@pytest.fixture
def peaks_file(tmp_path):
    """Create a Peaks.txt file and return the path."""
    path = tmp_path / "Peaks.txt"
    path.write_text("ref-001 - 30 70\ntgt-001 - 33 73\ntgt-002 - 28 68\n")
    return str(path)


@pytest.fixture
def ref_signal(sample_df):
    """Extract the reference signal as a numpy array."""
    features = sample_df.iloc[:, 3:]
    return pd.to_numeric(features.iloc[0], errors="coerce").fillna(0).values.astype(float)


@pytest.fixture
def tgt_signal(sample_df):
    """Extract target 1 signal as a numpy array."""
    features = sample_df.iloc[:, 3:]
    return pd.to_numeric(features.iloc[1], errors="coerce").fillna(0).values.astype(float)


@pytest.fixture
def scan_axis():
    """Return scan axis for 100 scan points."""
    return np.arange(100)
