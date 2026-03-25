# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

luv-align is a Python-based signal alignment pipeline for mass spectrometry / metabolomics data (Luventix). It aligns chromatographic sample signals to a reference sample using a two-step approach: anchor-peak-based variable shifting followed by Dynamic Time Warping (DTW).

## Pipeline

The scripts are meant to be run sequentially from the `data/` directory (input/output files use relative paths):

1. **`src/IdentPeaks.py`** — Peak identification. Plots a reference sample's signal and detects peaks using `scipy.signal.find_peaks`. Used to manually identify anchor peak scan numbers recorded in `data/Peaks.txt`.
2. **`src/Alignment.py`** — Core alignment. Performs two-phase alignment: (a) linear interpolation-based variable shift using manually identified anchor peaks, then (b) FastDTW fine alignment. Outputs aligned matrix as TSV.
3. **`src/PlotALL.py`** — Interactive visualization of aligned output using matplotlib with `mplcursors` hover tooltips.

## Running

```bash
cd data
python ../src/IdentPeaks.py    # identify anchor peaks visually
python ../src/Alignment.py     # run alignment pipeline
python ../src/PlotALL.py       # plot aligned results
```

## Dependencies

pandas, numpy, matplotlib, scipy, fastdtw, mplcursors

## Data Format

Input TSV files have metadata columns (sampleID, condition, diseasePresentFlag) followed by intensity values at each scan index (columns named by integer scan number). The `metadata_cols` parameter in each script controls how many leading columns are metadata.

## Architecture Notes

- All configuration is hardcoded as parameters at the top of each script (input/output filenames, sample IDs, anchor peak scan numbers, thresholds). There is no CLI argument parsing.
- `data/Peaks.txt` stores manually identified anchor peak scan numbers per sample in the format: `sampleID - peak1_scan peak2_scan`.
- Anchor peaks in `Alignment.py` must be manually transcribed from `Peaks.txt` into the `target_anchor_peaks` dict and `ref_peak1_scan`/`ref_peak2_scan` variables.
- The alignment reference sample is always the first entry in `sample_ids_to_plot`.
