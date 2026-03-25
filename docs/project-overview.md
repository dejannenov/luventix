# luv-align — Project Overview

## Purpose

Signal alignment pipeline for mass spectrometry / metabolomics data (Luventix). Aligns chromatographic sample signals to a reference sample using a two-step approach: anchor-peak-based variable shifting followed by Dynamic Time Warping (DTW).

## Repository Structure

- **Type:** Monolith
- **Primary Language:** Python
- **Architecture:** Sequential data pipeline (3-stage)

## Technology Stack

| Category | Technology | Notes |
|---|---|---|
| Language | Python 3.x | No version pinned |
| Data I/O | pandas, numpy | TSV format |
| Signal Processing | scipy | `find_peaks`, `interp1d` |
| Alignment | fastdtw | Fast Dynamic Time Warping |
| Visualization | matplotlib, mplcursors | Interactive hover tooltips |

## Pipeline Overview

```
IdentPeaks.py → Alignment.py → PlotALL.py
   (detect)       (align)        (visualize)
```

1. **IdentPeaks.py** — Detect peaks in a reference sample signal using `scipy.signal.find_peaks`. Visually identify anchor peak scan numbers and record them in `data/Peaks.txt`.
2. **Alignment.py** — Two-phase alignment: (a) linear interpolation variable shift using manually identified anchor peaks, (b) FastDTW fine alignment. Outputs aligned matrix as TSV.
3. **PlotALL.py** — Interactive matplotlib visualization of aligned output with `mplcursors` hover tooltips showing sample name, scan number, and intensity.

## Data Format

- **Input:** TSV with metadata columns (sampleID, condition, diseasePresentFlag) followed by intensity values at each scan index (columns named by integer scan number)
- **Aligned Output:** TSV with only sampleID + intensity columns (metadata columns dropped)
- **Peaks.txt:** `sampleID - peak1_scan peak2_scan` format

## Key Design Decisions

- All configuration is hardcoded at the top of each script — no CLI argument parsing
- Anchor peaks must be manually transcribed from `Peaks.txt` into `Alignment.py`
- Reference sample is always the first entry in `sample_ids_to_plot`
- Scripts must be run from the `data/` directory (relative file paths)

## Links

- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
