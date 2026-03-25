# luv-align — Project Documentation Index

## Project Overview

- **Type:** Monolith — single cohesive codebase
- **Primary Language:** Python
- **Architecture:** Sequential data pipeline (3-stage)

## Quick Reference

- **Tech Stack:** Python, pandas, numpy, scipy, fastdtw, matplotlib, mplcursors
- **Entry Points:** `src/IdentPeaks.py`, `src/Alignment.py`, `src/PlotALL.py`
- **Architecture Pattern:** Sequential file-based pipeline
- **Run From:** `data/` directory (relative paths)

## Generated Documentation

- [Project Overview](./project-overview.md) — Purpose, tech stack summary, pipeline overview
- [Architecture](./architecture.md) — System design, algorithms, data formats, limitations
- [Source Tree Analysis](./source-tree-analysis.md) — Directory structure, file dependencies
- [Development Guide](./development-guide.md) — Setup, running, configuration, workflow

## Existing Documentation

- [CLAUDE.md](../CLAUDE.md) — AI agent instructions and project guidance

## Getting Started

1. Install dependencies: `pip install pandas numpy matplotlib scipy fastdtw mplcursors`
2. Navigate to the data directory: `cd data`
3. Run the pipeline scripts in order:
   - `python ../src/IdentPeaks.py` — Identify anchor peaks
   - `python ../src/Alignment.py` — Run alignment
   - `python ../src/PlotALL.py` — Visualize results
4. See [Development Guide](./development-guide.md) for configuration details

---

*Generated: 2026-03-25 | Scan Level: Deep | Mode: Initial Scan*
