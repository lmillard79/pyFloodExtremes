# pyFloodExtremes

Bayesian flood frequency analysis for Australian catchments, built on PyMC and ArviZ.

`pyFloodExtremes` is a Python package for Bayesian flood frequency analysis. It implements three distribution families:
- **GEV (Generalized Extreme Value):** Single-population model.
- **LP3 (Log-Pearson Type 3):** Standard distribution for Australian Rainfall and Runoff (ARR).
- **TCEV (Two-Component Extreme Value):** A mixture model capable of capturing distinct flood-generating mechanisms (e.g., distinguishing ordinary floods from extraordinary events).

## Features
- Fully Bayesian inference via PyMC's NUTS sampler.
- High-quality ArviZ diagnostic trace and corner plots.
- Return level curves with 94% HDI uncertainty bands.
- Component separation probabilities for the TCEV mixture model.
- Seamless comparison of GEV, LP3, and TCEV return levels.
- Example Jupyter Notebooks for each model.

## Installation
This project uses `uv` for dependency management.
```bash
uv sync
```

## Quick Start
Check out the notebooks in the `notebooks/` directory for demonstrations using a 55-year annual maximum flow dataset containing a known outlier.
```bash
jupyter notebook notebooks/
```

## Testing
Run the test suite via pytest:
```bash
pytest tests/
```