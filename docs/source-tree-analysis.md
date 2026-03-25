# luv-align — Source Tree Analysis

## Directory Structure

```
luv-align/
├── CLAUDE.md                          # AI agent instructions
├── src/                               # Pipeline scripts
│   ├── IdentPeaks.py                  # Stage 1: Peak identification & visualization
│   ├── Alignment.py                   # Stage 2: Variable shift + DTW alignment
│   └── PlotALL.py                     # Stage 3: Interactive aligned signal plotting
├── data/                              # Working directory (run scripts from here)
│   ├── SIBO_Test_Set.tsv              # Input: raw sample intensity matrix
│   ├── luventix-data.tsv              # Additional input dataset
│   ├── Peaks.txt                      # Manually recorded anchor peak scan numbers
│   └── Aligned_SIBO_Test_Set.tsv      # Output: aligned intensity matrix
└── docs/                              # Generated project documentation
```

## Critical Folders

### `src/` — Pipeline Scripts

Contains the 3 sequential pipeline scripts. All are standalone, procedural Python files with no shared imports between them. Each script hardcodes its configuration at the top.

### `data/` — Working Directory

**This is the execution directory.** All scripts must be run from `data/` because they use relative file paths (e.g., `"SIBO_Test_Set.tsv"`). Contains both input data and pipeline outputs.

## File Dependency Graph

```
data/SIBO_Test_Set.tsv ──→ src/IdentPeaks.py ──→ [matplotlib plot]
                                                        │
                                                   (human inspects)
                                                        │
                                                        ▼
                                                  data/Peaks.txt
                                                        │
                                               (manually transcribed)
                                                        │
                                                        ▼
data/SIBO_Test_Set.tsv ──→ src/Alignment.py ──→ data/Aligned_SIBO_Test_Set.tsv
                                                        │
                                                        ▼
                           src/PlotALL.py ──→ [interactive matplotlib plot]
```

## Entry Points

All scripts are entry points — run directly with `python ../src/<script>.py` from the `data/` directory.
