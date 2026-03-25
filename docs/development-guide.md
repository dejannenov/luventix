# luv-align — Development Guide

## Prerequisites

- Python 3.x
- pip (Python package manager)

## Dependencies

Install required packages:

```bash
pip install pandas numpy matplotlib scipy fastdtw mplcursors
```

> **Note:** No `requirements.txt` or `pyproject.toml` exists yet. Versions are not pinned.

## Running the Pipeline

All scripts must be run from the `data/` directory:

```bash
cd data

# Stage 1: Identify peaks visually
python ../src/IdentPeaks.py

# Stage 2: Run alignment (after manually updating anchor peaks)
python ../src/Alignment.py

# Stage 3: Visualize aligned results
python ../src/PlotALL.py
```

## Configuration

Each script has hardcoded configuration variables at the top. There is no CLI argument parsing.

### IdentPeaks.py

| Variable | Default | Description |
|---|---|---|
| `input_file` | `"SIBO_Test_Set.tsv"` | Input data file |
| `metadata_cols` | `3` | Number of metadata columns |
| `sample_id_to_plot` | `'sibo-uk-6'` | Sample to analyze |

### Alignment.py

| Variable | Default | Description |
|---|---|---|
| `input_file` | `"SIBO_Test_Set.tsv"` | Input data file |
| `output_file` | `"Aligned_SIBO_Test_Set.tsv"` | Output file |
| `metadata_cols` | `3` | Metadata columns in input |
| `sample_ids_to_plot` | `['sibo-uk-6', ...]` | Samples to align (first = reference) |
| `intensity_threshold` | `0` | Minimum intensity to keep |
| `ref_peak1_scan` | `9949` | Reference anchor peak 1 scan number |
| `ref_peak2_scan` | `32429` | Reference anchor peak 2 scan number |
| `target_anchor_peaks` | `{...}` | Target sample anchor peak scan numbers |

### PlotALL.py

| Variable | Default | Description |
|---|---|---|
| `input_file` | `"Aligned_SIBO_Test_Set.tsv"` | Aligned data file |
| `metadata_cols` | `1` | Metadata columns in aligned output |

## Workflow for Adding New Samples

1. Add samples to the input TSV file
2. Run `IdentPeaks.py` with `sample_id_to_plot` set to the new sample
3. Record detected anchor peak scan numbers in `data/Peaks.txt`
4. Update `Alignment.py`:
   - Add sample ID to `sample_ids_to_plot`
   - Add anchor peaks to `target_anchor_peaks` dict
5. Run `Alignment.py`
6. Run `PlotALL.py` to verify alignment

## Testing

No test suite exists. Verification is done visually by inspecting the alignment plots.

## Code Style

- **File names:** PascalCase (e.g., `IdentPeaks.py`)
- **Variables:** snake_case
- **Structure:** Procedural — no classes, no `if __name__ == "__main__"` guards
- **Comments:** Section headers using `#SECTION NAME` or `# === Section Name ===`
- **No linter or formatter configured**
