# Test Suite Implementation Plan for pyFloodExtremes

Create minimal but meaningful test coverage for Bayesian flood frequency analysis functions, calibrated against real-world Australian AMS data.

## Overview

This plan implements Phase 2 testing requirements: smoke tests for core fit functions, unit tests for LH-moments, MGBT validation, and CI/CD via GitHub Actions.

## Test Calibration from Real Data

Based on analysis of real AMS data (Sites 1, 133 from paper dataset):
- **Flow ranges**: 0.2–13,087 m³/s across catchments
- **Typical 1% AEP quantiles**: 100–50,000 m³/s (covers small to large catchments)
- **Low outlier pattern**: Values ~10× lower than next lowest observation (e.g., Site 133: 0.2 m³/s vs. series median ~80 m³/s)

## Implementation Steps

### 2.1 Smoke Tests for Core Fit Functions

**File**: `tests/test_fitting.py`

Create smoke tests for `fit_gev` and `fit_lp3`:
- Generate 30 synthetic GEV samples with known parameters (mu=1000, sigma=300, xi=0.1)
- Call `fit_gev` with reduced draws (500) for test speed
- Assert `idata` contains expected variables: `mu`, `sigma`, `xi`
- Assert posterior median 1% AEP quantile falls within 100–50,000 m³/s range
- Repeat for `fit_lp3` with variables: `mu_Y`, `sigma_Y`, `gamma` (skew)
- Use synthetic data with known properties to ensure deterministic test behaviour

### 2.2 Unit Tests for LH-Moments Engine

**File**: `tests/test_lh_moments.py`

Implement three test categories:

**PWM Computation Test**:
- Use small known sample: [1.0, 2.0, 3.0, 4.0, 5.0]
- Calculate PWMs manually and verify `calculate_sample_pwms` matches within tolerance
- Assert b_0 equals sample mean, b_1 > b_0 for increasing data

**LH-Moment Fitting Test**:
- Generate synthetic GEV sample with known parameters (mu=500, sigma=150, xi=0.05)
- Fit using `fit_gev_lh` with shift=0
- Assert recovered parameters within 10% tolerance of true values
- Verify success flag is True

**Bootstrap CI Test**:
- Fit GEV to synthetic sample
- Run parametric bootstrap (100 simulations) for 1% AEP quantile
- Assert bootstrap CI brackets the fitted quantile (i.e., fitted value within CI bounds)

### 2.3 MGBT Smoke Test

**File**: `tests/test_mgbt.py`

Create two test scenarios:

**Obvious Low Outlier Test**:
- Construct series: 49 values from ~50–400 m³/s, plus one obvious outlier at 0.5 m³/s
- Call `detect_low_outliers`
- Assert `k_low >= 1` and the outlier index is in `outlier_indices`
- Assert `low_outlier_threshold` is above the outlier value

**Clean Series Test**:
- Use clean AMS data without obvious outliers (e.g., synthetic GEV sample)
- Call `detect_low_outliers`
- Assert `k_low == 0` and `outlier_indices` is empty

### 2.4 GitHub Actions CI

**File**: `.github/workflows/test.yml`

Create minimal workflow:
- Trigger on push to `main` and pull requests
- Use `ubuntu-latest` runner
- Checkout code with `actions/checkout@v4`
- Setup Python environment with `astral-sh/setup-uv@v4`
- Run `uv sync` to install dependencies
- Execute `uv run pytest tests/` with coverage reporting

## Key Design Decisions

1. **Synthetic data for fit tests**: Ensures deterministic, reproducible results without external data dependencies
2. **Reduced MCMC draws (500)**: Balances test coverage with CI execution time
3. **Calibrated thresholds**: Based on real AMS data ranges from paper dataset
4. **Tolerance-based assertions**: Accounts for MCMC sampling variability and numerical precision
5. **No external data dependencies**: All tests use synthetic or inline data to ensure portability

## Acceptance Criteria

- [ ] `pytest tests/` runs successfully with all tests passing
- [ ] Tests complete within 2 minutes (reduced MCMC draws)
- [ ] GitHub Actions workflow passes on push/PR
- [ ] Coverage report generated showing tested functions

