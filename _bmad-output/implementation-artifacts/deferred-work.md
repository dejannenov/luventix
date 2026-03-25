# Deferred Work

## From: spec-modernize-python-best-practices review

- **DTW path deduplication** — `align_with_dtw` passes raw DTW path indices to `interp1d` which may contain duplicates. Pre-existing from original code. Add `np.unique` dedup if issues arise on new datasets.
- **Zero-signal peak detection** — `detect_peaks` with all-zero signal produces `height=0` threshold. Add guard for `signal.max() <= 0`.
- **Empty DTW path** — `zip(*path, strict=True)` crashes on zero-length signals. Add length guard.
- **Single anchor peak** — `variable_shift_signal` requires >= 2 anchor peaks for `interp1d`. Add validation.
- **Malformed Peaks.txt** — Lines with < 2 scan numbers are silently dropped. Add warning logging.
