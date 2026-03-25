# luv-align — Architecture

## Executive Summary

luv-align is a 3-stage sequential data pipeline for aligning chromatographic mass spectrometry signals. It uses a procedural Python architecture with no framework, no ORM, and no web layer. Each stage is a standalone script that reads/writes TSV files.

## Architecture Pattern

**Sequential File-Based Pipeline**

```
[TSV Input] → IdentPeaks.py → [Peaks.txt (manual)]
[TSV Input] + [Peaks.txt] → Alignment.py → [Aligned TSV]
[Aligned TSV] → PlotALL.py → [Interactive Plot]
```

- No shared in-memory state between stages
- Each script is self-contained with its own data loading
- Inter-stage communication is through TSV files on disk
- Manual human intervention required between stage 1 and 2 (peak transcription)

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Data loading | pandas | TSV read/write, DataFrame manipulation |
| Numeric ops | numpy | Array operations, signal casting |
| Peak detection | scipy.signal.find_peaks | Automated peak finding with height/distance thresholds |
| Interpolation | scipy.interpolate.interp1d | Variable shift and DTW output resampling |
| Alignment | fastdtw | Dynamic Time Warping for fine alignment |
| Visualization | matplotlib | Static and interactive plotting |
| Interactivity | mplcursors | Hover tooltips on plot lines |

## Data Architecture

### Input Format (SIBO_Test_Set.tsv)

```
sampleID | condition | diseasePresentFlag | 1 | 2 | 3 | ... | N
---------|-----------|-------------------|---|---|---|-----|---
sibo-uk-6| ...       | ...               | 0 | 5 | 12| ... | 0
```

- First 3 columns are metadata (`metadata_cols = 3`)
- Remaining columns are integer scan numbers with intensity values
- Columns are cast to `int` after loading

### Aligned Output Format (Aligned_SIBO_Test_Set.tsv)

```
sampleID | 1 | 2 | 3 | ... | N
---------|---|---|---|-----|---
sibo-uk-6| 0 | 5 | 12| ... | 0
```

- Only 1 metadata column (`metadata_cols = 1`) — condition and diseasePresentFlag are dropped
- Intensity values are float (interpolated)

### Peaks.txt Format

```
sampleID - peak1_scan peak2_scan
```

- Manually created after visual inspection of IdentPeaks.py output
- Must be manually transcribed into `Alignment.py` variables

## Core Algorithms

### Stage 1: Peak Identification (IdentPeaks.py)

- Uses `scipy.signal.find_peaks` with `height=max*0.08` and `distance=50`
- Plots reference sample with annotated peak positions
- Purpose: human identifies anchor peaks for alignment

### Stage 2a: Variable Shift (Alignment.py)

- `variable_shift_signal()` function
- Uses `interp1d` to create a shift function from anchor peak correspondences
- Linearly interpolates shift across all scan positions
- Extrapolates beyond anchor peak range

### Stage 2b: DTW Fine Alignment (Alignment.py)

- `align_with_dtw()` function
- Uses `fastdtw` with custom scalar distance `abs(a - b)`
- Warping path is converted back to aligned signal via `interp1d`
- Out-of-range values filled with 0

### Stage 3: Visualization (PlotALL.py)

- Overlays all aligned sample signals
- Uses `mplcursors` for interactive hover showing sample name, scan, intensity
- Lines identified by `set_gid(sample_id)`

## Entry Points

| Script | Purpose | Run From |
|---|---|---|
| `src/IdentPeaks.py` | Peak identification | `data/` |
| `src/Alignment.py` | Signal alignment | `data/` |
| `src/PlotALL.py` | Result visualization | `data/` |

## Testing Strategy

No test suite exists. Scripts execute procedurally on import with no `if __name__ == "__main__"` guards. Adding tests would require:

1. Extracting functions into importable modules, or
2. Mocking `pd.read_csv` and `plt.show` to prevent side effects on import

## Known Limitations

- No automated parsing of `Peaks.txt` — anchor peaks must be manually transcribed
- No error handling for missing samples or malformed data
- No support for batch processing multiple datasets
- No CLI interface — all configuration is hardcoded
- Aligned output drops metadata columns
