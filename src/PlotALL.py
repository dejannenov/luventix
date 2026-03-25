"""Interactive visualization of aligned output with hover tooltips."""

import sys
from pathlib import Path

import matplotlib.pyplot as plt

# Ensure the package is importable when running from data/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from luv_align.config import PlotConfig
from luv_align.io import load_sample_matrix
from luv_align.plotting import plot_with_tooltips

# Parameters
config = PlotConfig()

# Load Data
df, scan_axis, features_df = load_sample_matrix(config.input_file, config.metadata_cols)

# Plot with interactive tooltips
plot_with_tooltips(df, features_df)
plt.show()
