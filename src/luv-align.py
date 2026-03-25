"""luv-align: Align chromatographic sample signals to a reference using FastDTW."""

import argparse
import sys
import zipfile
from pathlib import Path

# Ensure the package is importable when running from any directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from luv_align.alignment import align_with_dtw, apply_intensity_threshold
from luv_align.io import export_aligned_matrix, extract_multiple_signals, load_sample_matrix


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

    for sample_id in sample_ids[1:]:
        print(f"DTW aligning '{sample_id}' to reference '{ref_id}'...")
        aligned[sample_id] = apply_intensity_threshold(
            align_with_dtw(ref_signal, sample_signals[sample_id]), threshold=0
        )

    export_aligned_matrix(aligned, sample_ids, scan_axis, output_file)
    print(f"Aligned {len(sample_ids)} samples → {output_file}")


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
    args = parse_args(argv)

    # Detect metadata columns
    metadata_cols = detect_metadata_cols(args.input_file)

    # Load data
    df, scan_axis, features_df = load_sample_matrix(args.input_file, metadata_cols)

    # Get all sample IDs
    all_ids = df.iloc[:, 0].tolist()

    if args.full:
        # Align to every sample as reference
        sample_signals = extract_multiple_signals(df, features_df, all_ids)
        output_dir = args.output_file if args.output_file else str(Path(args.input_file).parent)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        for ref_id in all_ids:
            tsv_path = Path(output_dir) / f"{ref_id}-aligned.tsv"
            print(f"\n=== Aligning to reference: {ref_id} ===")
            align_to_reference(sample_signals, ref_id, all_ids, scan_axis, str(tsv_path))

            # Compress to zip and remove the TSV
            zip_path = tsv_path.with_suffix(".zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(tsv_path, tsv_path.name)
            tsv_path.unlink()
            print(f"Compressed → {zip_path}")

        print(f"\nDone. {len(all_ids)} zip files written to {output_dir}/")
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
        align_to_reference(sample_signals, args.align_to_id, all_ids, scan_axis, args.output_file)


if __name__ == "__main__":
    main()
