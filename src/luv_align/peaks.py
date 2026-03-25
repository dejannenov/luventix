"""Peak detection for chromatographic signals."""

import numpy as np
from scipy.signal import find_peaks


def detect_peaks(
    signal: np.ndarray,
    scan_axis: np.ndarray,
    height_fraction: float = 0.08,
    distance: int = 50,
) -> tuple[np.ndarray, np.ndarray]:
    """Detect peaks in a signal using scipy.signal.find_peaks.

    Args:
        signal: 1D intensity array.
        scan_axis: Corresponding scan number array.
        height_fraction: Minimum peak height as fraction of signal max.
        distance: Minimum distance between peaks in samples.

    Returns:
        Tuple of (peak_indices, peak_scan_numbers).
    """
    height_threshold = np.max(signal) * height_fraction
    peak_indices, _ = find_peaks(signal, height=height_threshold, distance=distance)
    return peak_indices, scan_axis[peak_indices]
