---
title: 'Modernize to Python Best Practices'
type: 'refactor'
created: '2026-03-25'
status: 'done'
baseline_commit: 'e5a7fde'
context: ['_bmad-output/project-context.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The pipeline is 3 monolithic procedural scripts with no dependency management, no tests, no linter, duplicated logic, and hardcoded config. Code executes on import making it untestable, and there's no virtual environment.

**Approach:** Create project infrastructure (venv, pyproject.toml, ruff linter), refactor into a `luv_align` package with focused modules and dataclass configs, add pytest with full coverage, and keep the 3 original entry-point scripts as thin wrappers.

## Boundaries & Constraints

**Always:**
- Preserve exact alignment behavior — same inputs must produce identical outputs
- Keep entry-point scripts runnable from `data/` directory (`python ../src/IdentPeaks.py`)
- Use `pyproject.toml` as single config source (deps, ruff, pytest, coverage)
- Use dataclasses for config (no pydantic or external config libs)
- Use ruff for linting+formatting (replaces flake8+black+isort)

**Ask First:**
- Adding CLI argument parsing (argparse) to entry scripts
- Changing the `Peaks.txt` manual transcription workflow
- Adding type hints beyond function signatures

**Never:**
- Break backwards compatibility of TSV input/output formats
- Add heavy frameworks (click, pydantic, poetry)
- Change the two-phase alignment algorithm
- Auto-parse `Peaks.txt` into `Alignment.py` (that's a separate feature)

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Alignment round-trip | SIBO_Test_Set.tsv + current anchor peaks | Aligned TSV identical to current output | N/A |
| Missing sample ID | sample_id not in TSV | Raise ValueError with clear message | Test asserts exception |
| Empty signal | All-zero intensity row | Aligned output is all zeros | Passes through cleanly |
| Linter clean | All source files | `ruff check` exits 0 | CI-ready |
| Full coverage | pytest --cov | >= 90% line coverage | Fail if below threshold |

</frozen-after-approval>

## Code Map

- `pyproject.toml` -- project metadata, deps, ruff config, pytest config, coverage config
- `src/luv_align/__init__.py` -- package init
- `src/luv_align/config.py` -- dataclass configs (IdentPeaksConfig, AlignmentConfig, PlotConfig)
- `src/luv_align/io.py` -- TSV loading, signal extraction, matrix export, Peaks.txt parsing
- `src/luv_align/peaks.py` -- peak detection via scipy.signal.find_peaks
- `src/luv_align/alignment.py` -- variable_shift_signal, align_with_dtw, threshold
- `src/luv_align/plotting.py` -- matplotlib/mplcursors plotting functions
- `src/IdentPeaks.py` -- thin entry-point wrapper (kept for backwards compat)
- `src/Alignment.py` -- thin entry-point wrapper
- `src/PlotALL.py` -- thin entry-point wrapper
- `tests/conftest.py` -- shared fixtures (sample data, temp files)
- `tests/test_io.py` -- DataIO tests
- `tests/test_peaks.py` -- PeakDetector tests
- `tests/test_alignment.py` -- Aligner tests
- `tests/test_plotting.py` -- Plotter tests (mock plt.show)
- `tests/test_config.py` -- Config dataclass tests

## Tasks & Acceptance

**Execution:**
- [x] `pyproject.toml` -- Create with project metadata, dependencies (pandas, numpy, scipy, fastdtw, matplotlib, mplcursors), dev dependencies (pytest, pytest-cov, ruff), ruff config, pytest config with coverage threshold
- [x] `src/luv_align/__init__.py` -- Create package init with version
- [x] `src/luv_align/config.py` -- Create dataclass configs for each pipeline stage
- [x] `src/luv_align/io.py` -- Extract shared data loading, signal extraction, matrix export, Peaks.txt loading
- [x] `src/luv_align/peaks.py` -- Extract peak detection logic from IdentPeaks.py
- [x] `src/luv_align/alignment.py` -- Extract variable_shift_signal and align_with_dtw from Alignment.py
- [x] `src/luv_align/plotting.py` -- Extract plotting logic, peak annotation, mplcursors tooltips
- [x] `src/IdentPeaks.py` -- Refactor to thin wrapper importing from luv_align package
- [x] `src/Alignment.py` -- Refactor to thin wrapper importing from luv_align package
- [x] `src/PlotALL.py` -- Refactor to thin wrapper importing from luv_align package
- [x] `tests/conftest.py` -- Create shared fixtures with small synthetic test data
- [x] `tests/test_io.py` -- Test load_sample_matrix, extract_signal, export_aligned_matrix
- [x] `tests/test_peaks.py` -- Test detect_peaks, load_peaks_file
- [x] `tests/test_alignment.py` -- Test variable_shift_signal, align_with_dtw, threshold
- [x] `tests/test_plotting.py` -- Test plot functions with mocked plt.show
- [x] `tests/test_config.py` -- Test config dataclass defaults and validation
- [x] Run `ruff check src/ tests/` -- Verify zero lint errors
- [x] Run `pytest --cov=luv_align --cov-fail-under=90` -- Verify full coverage

**Acceptance Criteria:**
- Given the refactored package, when running `cd data && python ../src/Alignment.py`, then output TSV is produced with identical format to current output
- Given all source files, when running `ruff check src/ tests/`, then exit code is 0
- Given the test suite, when running `pytest --cov=luv_align --cov-fail-under=90`, then all tests pass with >= 90% coverage
- Given the venv, when running `pip install -e ".[dev]"`, then all deps install cleanly

## Design Notes

**Package layout:** Using `src/luv_align/` inside existing `src/` keeps entry scripts at `src/IdentPeaks.py` (backwards compat) while the package lives alongside. Entry scripts add `src/` to path or rely on editable install.

**Config pattern:** Dataclasses with defaults matching current hardcoded values. No config file parsing — just Python objects. Entry scripts instantiate configs inline.

**Test data:** Synthetic fixtures with 3-5 samples × 100 scan points. No real data files in tests. Peaks and alignment verified numerically against known transforms.

## Verification

**Commands:**
- `pip install -e ".[dev]"` -- expected: clean install, no errors
- `ruff check src/ tests/` -- expected: exit 0, no violations
- `ruff format --check src/ tests/` -- expected: exit 0, already formatted
- `pytest --cov=luv_align --cov-fail-under=90 -v` -- expected: all pass, >= 90% coverage
- `cd data && python ../src/Alignment.py` -- expected: produces Aligned_SIBO_Test_Set.tsv

## Spec Change Log


## Suggested Review Order

**Package architecture**

- Dataclass configs with defaults matching original hardcoded values
  [`config.py:1`](../../src/luv_align/config.py#L1)

- Shared TSV loading, signal extraction, and Peaks.txt parser
  [`io.py:1`](../../src/luv_align/io.py#L1)

- Two-phase alignment: variable shift + FastDTW, extracted as pure functions
  [`alignment.py:1`](../../src/luv_align/alignment.py#L1)

- Peak detection wrapper around scipy.signal.find_peaks
  [`peaks.py:1`](../../src/luv_align/peaks.py#L1)

- Plotting functions returning Figure objects instead of calling plt.show
  [`plotting.py:1`](../../src/luv_align/plotting.py#L1)

**Entry script refactors**

- Core pipeline script — now 35 lines importing from luv_align
  [`Alignment.py:1`](../../src/Alignment.py#L1)

- Peak identification — thin wrapper over io + peaks + plotting
  [`IdentPeaks.py:1`](../../src/IdentPeaks.py#L1)

- Visualization — thin wrapper over io + plotting with tooltips
  [`PlotALL.py:1`](../../src/PlotALL.py#L1)

**Infrastructure**

- Single config source: deps, ruff, pytest, coverage all in one file
  [`pyproject.toml:1`](../../pyproject.toml#L1)

**Tests**

- Synthetic fixtures: 3 samples x 100 scans with known peak positions
  [`conftest.py:1`](../../tests/conftest.py#L1)

- Alignment tests: shift, DTW, threshold, full pipeline
  [`test_alignment.py:1`](../../tests/test_alignment.py#L1)

- I/O tests: load, extract, export round-trip, peaks file parsing
  [`test_io.py:1`](../../tests/test_io.py#L1)

- Peak detection tests: known peaks, flat signal, distance filtering
  [`test_peaks.py:1`](../../tests/test_peaks.py#L1)

- Plotting tests: figure creation, axis labels, GID tooltips
  [`test_plotting.py:1`](../../tests/test_plotting.py#L1)

- Config tests: defaults, custom values, mutable default independence
  [`test_config.py:1`](../../tests/test_config.py#L1)
