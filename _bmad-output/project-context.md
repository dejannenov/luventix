---
project_name: 'luv-align'
user_name: 'Dejan'
date: '2026-03-25'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'quality_rules', 'workflow_rules', 'anti_patterns']
status: 'complete'
rule_count: 20
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Language:** Python 3.x (no version pinned)
- **Data:** pandas, numpy — TSV file I/O
- **Visualization:** matplotlib, mplcursors (interactive hover tooltips)
- **Signal Processing:** scipy (find_peaks, interp1d)
- **Alignment:** fastdtw (Fast Dynamic Time Warping)
- **Dependency Management:** None — no requirements.txt or pyproject.toml exists. Agents adding dependencies should create a requirements.txt.

## Critical Implementation Rules

### Language-Specific Rules

- All scripts are **procedural/imperative** — no classes, no `if __name__ == "__main__"` guards. Functions are defined inline and called immediately.
- Configuration is done via **hardcoded variables at the top of each script** — there is no CLI argument parsing (`argparse`, `click`, etc.). New scripts must follow this pattern unless explicitly told otherwise.
- Duplicate imports exist in the codebase (e.g., `find_peaks` imported twice in `IdentPeaks.py`) — agents should clean these up when touching a file but not proactively refactor untouched files.
- `pd.to_numeric(..., errors='coerce').fillna(0)` is the standard pattern for converting intensity columns to numeric. Always use this when reading signal data.
- Signals must be explicitly cast: `np.ravel(signal).astype(float)` before passing to alignment functions. FastDTW and scipy interpolation can fail on unexpected dtypes or shapes.

### Framework-Specific Rules (scipy / fastdtw / matplotlib)

- **fastdtw** requires a custom scalar distance function: `def scalar_distance(a, b): return abs(a - b)`. Do not pass a string metric name.
- **interp1d** is used with `fill_value=0` and `bounds_error=False` for out-of-range extrapolation — this zeros out edges rather than raising errors. Maintain this convention.
- **matplotlib** figures use `figsize=(14, 7)` or `(16, 6)` as standard sizes. Use `plt.tight_layout()` before `plt.show()`.
- **mplcursors** hover tooltips use `sel.artist.get_gid()` to retrieve the sample name — lines must have `.set_gid(sample_id)` set during plotting.

### Testing Rules

- **No test suite exists.** There are no unit or integration tests for the pipeline scripts.
- If adding tests, note that scripts have no function-level modularity — they execute on import. Tests would need to either refactor into callable functions or mock `pd.read_csv` / `plt.show`.

### Code Quality & Style Rules

- **File naming:** PascalCase for script names (`IdentPeaks.py`, `Alignment.py`, `PlotALL.py`)
- **Variable naming:** snake_case throughout
- **Section comments:** Use `#SECTION NAME` or `# === Section Name ===` style headers to delineate logical blocks within scripts
- **No docstrings** on functions — inline comments only where non-obvious
- **No linter or formatter configured** — no `.flake8`, `pyproject.toml [tool.black]`, etc.

### Development Workflow Rules

- **Working directory matters:** All scripts assume they are run from the `data/` directory. File paths like `"SIBO_Test_Set.tsv"` are relative to `data/`.
- **Pipeline is sequential:** `IdentPeaks.py` -> `Alignment.py` -> `PlotALL.py`. Each script's output is the next script's input.
- **Single branch so far** — `main` branch with one commit. No branching conventions established yet.

### Critical Don't-Miss Rules

- **Anchor peaks are manually transcribed.** The `Peaks.txt` file format is `sampleID - peak1_scan peak2_scan`. These values must be manually copied into `Alignment.py`'s `target_anchor_peaks` dict and `ref_peak1_scan`/`ref_peak2_scan` variables. There is no automated parsing of `Peaks.txt`.
- **Reference sample is always `sample_ids_to_plot[0]`.** The first entry in the list is treated as the alignment reference. Reordering this list changes which sample everything aligns to.
- **`metadata_cols` varies between scripts.** `IdentPeaks.py` and `Alignment.py` use `metadata_cols = 3` (sampleID, condition, diseasePresentFlag). `PlotALL.py` uses `metadata_cols = 1` because the aligned output only has sampleID. Agents must check which input file a script reads to set this correctly.
- **Aligned output loses metadata.** `Alignment.py` outputs only `sampleID` + intensity columns — the `condition` and `diseasePresentFlag` columns are dropped. Any downstream script reading aligned data must account for this.
- **Scan columns are integers.** Column headers in the TSV are scan numbers cast to `int`. Code like `features_df.columns = features_df.columns.astype(int)` is required after loading. The aligned output file uses `.str.strip()` before `.astype(int)` to handle whitespace.
- **Never add `plt.show()` blocking calls in non-interactive/CI contexts.** The pipeline is designed for interactive use with matplotlib's GUI backend.

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review periodically for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-03-25
