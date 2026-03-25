"""High-level pipeline functions for alignment, compression, and parallel execution."""

import lzma
import math
import os
import time
from pathlib import Path

from luv_align.alignment import align_with_dtw, apply_intensity_threshold
from luv_align.io import export_aligned_matrix


def align_to_reference(
    sample_signals: dict[str, object],
    ref_id: str,
    all_ids: list[str],
    scan_axis: object,
    output_file: str,
) -> None:
    """Align all samples to a single reference and export."""
    ref_signal = sample_signals[ref_id]
    sample_ids = [ref_id] + [sid for sid in all_ids if sid != ref_id]
    aligned = {ref_id: ref_signal.copy()}

    targets = sample_ids[1:]
    total = len(targets)
    for n, sample_id in enumerate(targets, 1):
        print(f"  [{n} of {total}] DTW aligning '{sample_id}' to reference '{ref_id}'...")
        aligned[sample_id] = apply_intensity_threshold(
            align_with_dtw(ref_signal, sample_signals[sample_id]), threshold=0
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
) -> str:
    """Align all samples to one reference, export, compress to xz, and remove the TSV.

    Designed to run in a worker process. Returns a status message.
    """
    t0 = time.monotonic()
    tsv_path = Path(output_dir) / f"{ref_id}-aligned.tsv"
    print(f"\n=== [{n} of {total}] Aligning to reference: {ref_id} ===")
    align_to_reference(sample_signals, ref_id, all_ids, scan_axis, str(tsv_path))

    xz_path = tsv_path.with_suffix(".tsv.xz")
    tsv_size = tsv_path.stat().st_size
    with open(tsv_path, "rb") as f_in, lzma.open(xz_path, "wb", preset=9) as f_out:
        f_out.write(f_in.read())
    xz_size = xz_path.stat().st_size
    tsv_path.unlink()

    elapsed = time.monotonic() - t0
    ratio = (1 - xz_size / tsv_size) * 100 if tsv_size > 0 else 0
    return (
        f"[{n} of {total}] {ref_id}: {elapsed:.1f}s, "
        f"compressed {tsv_size // 1024}KB → {xz_size // 1024}KB ({ratio:.0f}% reduction)"
    )


def get_worker_count() -> int:
    """Return the number of parallel workers: 75% of CPU cores, minimum 1."""
    return max(1, math.floor(os.cpu_count() * 0.75))
