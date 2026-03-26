"""High-level pipeline functions for alignment, compression, and parallel execution."""

import lzma
import math
import os
import time
from pathlib import Path

from luv_align.alignment import align_with_dtw, apply_intensity_threshold
from luv_align.io import export_aligned_matrix


def _counter(n: int, total: int) -> str:
    """Format a counter like ``[  3 of 100]`` with right-aligned numbers."""
    width = len(str(total))
    return f"[{n:>{width}} of {total}]"


def align_to_reference(
    sample_signals: dict[str, object],
    ref_id: str,
    all_ids: list[str],
    scan_axis: object,
    output_file: str,
    use_full_dtw: bool = False,
    file_label: str = "",
    radius: int = 1,
) -> None:
    """Align all samples to a single reference and export."""
    ref_signal = sample_signals[ref_id]
    sample_ids = [ref_id] + [sid for sid in all_ids if sid != ref_id]
    aligned = {ref_id: ref_signal.copy()}
    dtw_label = "full DTW" if use_full_dtw else "FastDTW"
    prefix = f"{file_label} " if file_label else ""

    targets = sample_ids[1:]
    total = len(targets)
    for n, sample_id in enumerate(targets, 1):
        print(
            f"  {prefix}{_counter(n, total)} {dtw_label} aligning "
            f"'{sample_id}' to reference '{ref_id}'..."
        )
        aligned[sample_id] = apply_intensity_threshold(
            align_with_dtw(ref_signal, sample_signals[sample_id], use_full_dtw, radius=radius),
            threshold=0,
        )

    export_aligned_matrix(aligned, sample_ids, scan_axis, output_file)
    print(f"Aligned {len(sample_ids)} samples → {output_file}")


def align_and_compress(
    sample_signals: dict[str, object],
    ref_id: str,
    all_ids: list[str],
    scan_axis: object,
    output_dir: str,
    n: int,
    total: int,
    use_full_dtw: bool = False,
    radius: int = 1,
) -> str:
    """Align all samples to one reference, export, compress to xz, and remove the TSV.

    Designed to run in a worker process. Returns a status message.
    """
    t0 = time.monotonic()
    tsv_path = Path(output_dir) / f"{ref_id}-aligned.tsv"
    tag = _counter(n, total)
    print(f"\n=== {tag} Aligning to reference: {ref_id} ===")
    align_to_reference(
        sample_signals, ref_id, all_ids, scan_axis, str(tsv_path), use_full_dtw, tag,
        radius=radius,
    )

    xz_path = tsv_path.with_suffix(".tsv.xz")
    tsv_size = tsv_path.stat().st_size
    print(f"  {tag} Compressing {ref_id} ({tsv_size // 1024}KB)...", flush=True)
    # preset 6 is the default; preset 9 uses ~600MB RAM per stream which
    # compounds badly when multiple workers compress in parallel.
    # Stream in chunks to avoid loading the entire TSV into memory.
    with open(tsv_path, "rb") as f_in, lzma.open(xz_path, "wb", preset=6) as f_out:
        while chunk := f_in.read(1024 * 1024):
            f_out.write(chunk)
    xz_size = xz_path.stat().st_size
    tsv_path.unlink()

    elapsed = time.monotonic() - t0
    ratio = (1 - xz_size / tsv_size) * 100 if tsv_size > 0 else 0
    return (
        f"{tag} {ref_id}: {elapsed:.1f}s, "
        f"compressed {tsv_size // 1024}KB → {xz_size // 1024}KB ({ratio:.0f}% reduction)"
    )


def get_worker_count(use_full_dtw: bool = False) -> int:
    """Return the number of parallel workers.

    For FastDTW: 75% of CPU cores (CPU-bound).
    For full DTW: cap at 2 workers to avoid memory exhaustion — the full
    O(N^2) cost matrix can consume tens of GB per alignment.
    """
    if use_full_dtw:
        return min(2, os.cpu_count() or 1)
    return max(1, math.floor(os.cpu_count() * 0.75))
