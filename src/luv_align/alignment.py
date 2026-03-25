"""Signal alignment via anchor-peak variable shift and DTW."""

import numpy as np
from scipy.interpolate import interp1d


def _scalar_distance(a: float, b: float) -> float:
    return abs(a - b)


def variable_shift_signal(
    signal: np.ndarray,
    ref_peaks: list[int],
    tgt_peaks: list[int],
) -> np.ndarray:
    """Apply variable shift to align a signal using anchor peak correspondences.

    Uses linear interpolation between anchor peak pairs to compute a
    position-dependent shift, then resamples the signal accordingly.
    """
    scan_indices = np.arange(len(signal))
    ref_arr = np.array(ref_peaks)
    tgt_arr = np.array(tgt_peaks)

    shift_function = interp1d(tgt_arr, ref_arr - tgt_arr, kind="linear", fill_value="extrapolate")
    variable_shifts = shift_function(scan_indices)

    f = interp1d(scan_indices, signal, kind="linear", bounds_error=False, fill_value=0)
    return f(scan_indices - variable_shifts)


def _deduplicate_path(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Deduplicate DTW path indices by averaging y-values at repeated x-values.

    FastDTW can map multiple reference indices to the same target index,
    producing duplicate x-values that cause division-by-zero in interp1d.
    """
    unique_x, inverse = np.unique(x, return_inverse=True)
    # Sum y-values per unique x, then divide by count
    sum_y = np.zeros(len(unique_x), dtype=np.float64)
    np.add.at(sum_y, inverse, y)
    counts = np.zeros(len(unique_x), dtype=np.int64)
    np.add.at(counts, inverse, 1)
    return unique_x, sum_y / counts


def align_with_dtw(
    ref: np.ndarray, target: np.ndarray, use_full_dtw: bool = False, radius: int = 1
) -> np.ndarray:
    """Align target signal to reference using DTW.

    Args:
        ref: Reference signal.
        target: Target signal to align.
        use_full_dtw: If True, use the full O(N^2) DTW algorithm (dtw-python)
            for maximum accuracy. If False (default), use FastDTW which is
            approximate but much faster.
        radius: FastDTW accuracy radius (default 1). Higher values explore
            more of the cost matrix for better accuracy. Ignored when
            use_full_dtw is True.

    Returns the warped target signal resampled to match the reference length.
    """
    ref = np.ravel(ref).astype(float)
    target = np.ravel(target).astype(float)

    max_radius = len(ref) // 4
    if not use_full_dtw and radius > max_radius:
        raise ValueError(
            f"radius={radius} exceeds maximum allowed value of {max_radius} "
            f"(1/4 of signal length {len(ref)})"
        )

    if use_full_dtw:
        from dtw import dtw as full_dtw

        alignment = full_dtw(ref, target, dist_method="euclidean")
        ref_indices = alignment.index1
        target_indices = alignment.index2
    else:
        from fastdtw import fastdtw

        _, path = fastdtw(ref, target, radius=radius, dist=_scalar_distance)
        ref_indices, target_indices = zip(*path, strict=True)

    tgt_arr = np.array(target_indices)

    unique_x, avg_y = _deduplicate_path(tgt_arr, target[tgt_arr])
    interp_func = interp1d(
        unique_x,
        avg_y,
        kind="linear",
        bounds_error=False,
        fill_value=0,
    )
    return interp_func(np.arange(len(ref)))


def apply_intensity_threshold(signal: np.ndarray, threshold: float) -> np.ndarray:
    """Zero out values below the intensity threshold."""
    return np.where(signal >= threshold, signal, 0)


def align_all_samples(
    ref_signal: np.ndarray,
    sample_signals: dict[str, np.ndarray],
    ref_id: str,
    target_anchor_peaks: dict[str, tuple[int, int]],
    ref_peaks: list[int],
    intensity_threshold: float = 0,
    use_full_dtw: bool = False,
    radius: int = 1,
) -> dict[str, np.ndarray]:
    """Run the full two-phase alignment pipeline on all samples.

    Phase 1: Variable shift using anchor peaks.
    Phase 2: FastDTW fine alignment.
    Then apply intensity threshold.
    """
    aligned = {ref_id: ref_signal.copy()}

    # Phase 1: Variable shift
    for sample_id, signal in sample_signals.items():
        if sample_id == ref_id:
            continue
        if sample_id in target_anchor_peaks:
            tgt_peak1, tgt_peak2 = target_anchor_peaks[sample_id]
            signal = variable_shift_signal(
                signal, ref_peaks=ref_peaks, tgt_peaks=[tgt_peak1, tgt_peak2]
            )
        aligned[sample_id] = signal

    # Phase 2: DTW fine alignment
    for sample_id in list(aligned):
        if sample_id == ref_id:
            continue
        aligned[sample_id] = align_with_dtw(ref_signal, aligned[sample_id], use_full_dtw, radius=radius)

    # Threshold
    for sample_id in aligned:
        aligned[sample_id] = apply_intensity_threshold(aligned[sample_id], intensity_threshold)

    return aligned
