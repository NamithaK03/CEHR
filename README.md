# CEHR: exact-length collision-aware hierarchical tube rearrangement

Code and aggregate results for the manuscript "CEHR: Exact-Length Collision-Aware Hierarchical Tube Rearrangement for Surveillance Video Synopsis."

## Contents
- `scripts/run_hierarchical_trial.py`: two-group (pair) refinement stage, run on the recorded single-group placements.
- `scripts/cached_refinement.py`: cached single-group refinement and the cached-versus-uncached equivalence and timing check.
- `scripts/make_figures.py`: regenerates the figures from the result files.
- `results/`: aggregate CSV outputs (paired runs, timing, robustness, cube-stage replay, cached refinement, fixed-target runs).

## Status
- The track-selection code (`pceo_heldout_trial/run.py`) is not yet included; its rule is described in the manuscript (Section VI, Dataset).
- The scripts read input data from a local data directory (`/mnt/data`) that is not included. The SynoClip source videos and annotations are those described in the FGS paper (Malekpour et al.); the exact annotation files used are not included here.
- The scripts were not re-executed as part of this packaging.
