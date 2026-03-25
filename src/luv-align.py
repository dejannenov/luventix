"""luv-align: Align chromatographic sample signals to a reference using FastDTW."""

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# Ensure the package is importable when running from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from luv_align.io import _format_size, extract_multiple_signals, load_sample_matrix
from luv_align.pipeline import align_and_compress, align_to_reference, get_worker_count


def detect_metadata_cols(filepath: str) -> int:
    """Detect the number of metadata columns by finding the first numeric column header."""
    import pandas as pd

    df = pd.read_csv(filepath, sep="\t", nrows=0, low_memory=False)
    for i, col in enumerate(df.columns):
        try:
            int(str(col).strip())
            return i
        except ValueError:
            continue
    raise ValueError(f"No numeric scan columns found in '{filepath}'")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="luv-align",
        description=(
            "Align chromatographic sample signals to a reference sample using FastDTW. "
            "Reads a TSV matrix where the first column contains sample IDs and remaining "
            "non-metadata columns contain intensity values at each scan index. "
            "All samples are aligned to the specified reference sample via "
            "Dynamic Time Warping and exported as a new TSV."
        ),
    )
    parser.add_argument(
        "--in",
        dest="input_file",
        required=True,
        help="Path to the input TSV file containing the sample intensity matrix.",
    )
    parser.add_argument(
        "--out",
        dest="output_file",
        default=None,
        help=(
            "In single mode: path for the output aligned TSV file. "
            "In --full mode: optional output directory for the aligned files "
            "(defaults to the input file's directory)."
        ),
    )
    parser.add_argument(
        "--align-to-id",
        default=None,
        help=(
            "Sample ID of the reference row to align all other samples to. "
            "Must match a value in the first column of the input file. "
            "Required unless --full is specified."
        ),
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help=(
            "Align to every sample as reference, producing one output file per sample. "
            "Output files are named <sample-id>-aligned.tsv in the input file's directory "
            "(or the directory specified by --out). Cannot be used with --align-to-id."
        ),
    )

    args = parser.parse_args(argv)

    if args.full:
        if args.align_to_id is not None:
            parser.error("--align-to-id cannot be used with --full")
    else:
        if args.output_file is None:
            parser.error("--out is required unless --full is specified")
        if args.align_to_id is None:
            parser.error("--align-to-id is required unless --full is specified")

    return args


def main(argv: list[str] | None = None) -> None:
    """Run the alignment pipeline."""
    pipeline_start = time.monotonic()
    args = parse_args(argv)

    input_path = Path(args.input_file)
    file_size = input_path.stat().st_size
    print(f"Input: {input_path} ({_format_size(file_size)})", flush=True)

    # Detect metadata columns
    print("Detecting metadata columns...", flush=True)
    metadata_cols = detect_metadata_cols(args.input_file)
    print(f"Found {metadata_cols} metadata column(s)", flush=True)

    # Load data
    df, scan_axis, features_df = load_sample_matrix(args.input_file, metadata_cols)

    # Get all sample IDs
    all_ids = df.iloc[:, 0].tolist()

    if args.full:
        # Align to every sample as reference
        sample_signals = extract_multiple_signals(df, features_df, all_ids)

        # Release DataFrames — signals are now in numpy arrays
        del df, features_df

        output_dir = args.output_file if args.output_file else str(Path(args.input_file).parent)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        total = len(all_ids)
        workers = get_worker_count()
        signal_mem = sum(s.nbytes for s in sample_signals.values())
        print(
            f"\nStarting parallel alignment: {total} references, "
            f"{workers} workers ({os.cpu_count()} cores), "
            f"signal data: {_format_size(signal_mem)}",
            flush=True,
        )
        print(
            f"Each worker receives ~{_format_size(signal_mem)} of signal data\n",
            flush=True,
        )

        align_start = time.monotonic()
        completed = 0
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    align_and_compress,
                    sample_signals, ref_id, all_ids, scan_axis,
                    output_dir, n, total,
                ): ref_id
                for n, ref_id in enumerate(all_ids, 1)
            }
            for future in as_completed(futures):
                completed += 1
                print(future.result(), flush=True)

        align_elapsed = time.monotonic() - align_start
        total_elapsed = time.monotonic() - pipeline_start
        print(
            f"\nDone. {total} xz files written to {output_dir}/"
            f"\nAlignment: {align_elapsed:.1f}s | Total pipeline: {total_elapsed:.1f}s",
            flush=True,
        )
    else:
        # Single reference alignment
        if args.align_to_id not in all_ids:
            print(
                f"Error: reference ID '{args.align_to_id}' not found in input file.",
                file=sys.stderr,
            )
            print(f"Available IDs: {', '.join(all_ids)}", file=sys.stderr)
            sys.exit(1)

        sample_signals = extract_multiple_signals(df, features_df, all_ids)
        del df, features_df

        print(f"\nAligning all samples to reference '{args.align_to_id}'...", flush=True)
        align_start = time.monotonic()
        align_to_reference(sample_signals, args.align_to_id, all_ids, scan_axis, args.output_file)
        total_elapsed = time.monotonic() - pipeline_start
        print(f"Total pipeline: {total_elapsed:.1f}s", flush=True)


if __name__ == "__main__":
    main()
