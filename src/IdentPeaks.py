"""Peak identification — detect and visualize peaks in a reference sample."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Ensure the package is importable when running from data/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from luv_align.config import IdentPeaksConfig
from luv_align.io import extract_signal, load_sample_matrix
from luv_align.peaks import detect_peaks
from luv_align.plotting import plot_signal_with_peaks

# Parameters
config = IdentPeaksConfig()

# Load Data
df, scan_axis, features_df = load_sample_matrix(config.input_file, config.metadata_cols)

# Extract Raw Signal
ref_signal = extract_signal(df, features_df, config.sample_id_to_plot)

# Detect Peaks
peak_indices, _ = detect_peaks(
    ref_signal, scan_axis, config.peak_height_fraction, config.peak_distance
)

# Plot
plot_signal_with_peaks(ref_signal, scan_axis, config.sample_id_to_plot, peak_indices)
plt.show()
