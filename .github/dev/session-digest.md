# pyFloodExtremes — Session Digest & Current State

This document captures the development work completed in Gemini CLI sessions on 2026-04-03, supplementing the original `handoffPlan.md`. It records what was built, what changed from the original plan, what is broken, and what remains to be done.

---

## Current State of the Codebase

All modules from the original plan are **implemented**. The project is largely functional but has known issues (see below).

### Module Status

| File | Status | Notes |
|---|---|---|
| `src/flood_ffa/gev/fit.py` | Done | PyTensor-native GEV logp, `pm.CustomDist` |
| `src/flood_ffa/gev/plots.py` | Done | `probscale` AEP axis, Cunnane positions, HDI band |
| `src/flood_ffa/lp3/fit.py` | Done | PyTensor-native P3 logp, fits in log-space |
| `src/flood_ffa/lp3/plots.py` | Done | Back-transforms to m3/s before plotting |
| `src/flood_ffa/tcev/fit.py` | Done | Mixture logsumexp logp, `pm.Potential` ordering constraint |
| `src/flood_ffa/tcev/plots.py` | Done | Numerical CDF inversion for return levels, component separation plot |
| `src/flood_ffa/compare.py` | Done | Overlaid three-model return level plot |
| `src/flood_ffa/preprocessing/mgbt.py` | Experimental | Ported from `E:\GitHub\MGBT_1.0.7\pymgbt`. Works for artificial outlier test; not formally validated against R reference output |
| `src/flood_ffa/stats/lh_moments.py` | Done | Sample PWMs, LH-moments (eta 0–4), theoretical GEV/LP3 PWMs via `scipy.integrate` |
| `src/flood_ffa/stats/bootstrap.py` | Done | Parametric bootstrap, 5th/95th percentile limits |
| `src/flood_ffa/gev/fit_lh.py` | Done | LH-moment GEV fitting, `scipy.optimize.least_squares` |
| `src/flood_ffa/lp3/fit_lh.py` | Done | LH-moment LP3 fitting, `scipy.optimize.least_squares` |
| `src/flood_ffa/flike.py` | Done | FLIKE orchestrator class: MGBT → LH-moments → shift selection → bootstrap |
| `src/flood_ffa/plots_lh.py` | Done | FLIKE-style AEP probability plot with bootstrap limits |

### Notebook Status

| Notebook | Executed | HTML Export | Notes |
|---|---|---|---|
| `01_gev_demo.ipynb` | Yes | Unconfirmed | Runs cleanly |
| `02_lp3_demo.ipynb` | Yes | Unconfirmed | Runs cleanly |
| `03_tcev_demo.ipynb` | Yes | Unconfirmed | "Scientific Narrative" cell is **empty** — see below |
| `04_comparison.ipynb` | Yes | Unconfirmed | Runs cleanly |
| `05_mgbt_demo.ipynb` | Yes | Unconfirmed | Runs cleanly |
| `06_flike_emulator.ipynb` | Uncertain | Missing | LP3 section had `RuntimeError`; solver was patched but re-execution timed out before confirmation |

---

## Key Departures from the Original Handoff Plan

### 1. PyMC GEV — `pm.CustomDist` not `pm.GEV`
The original plan proposed `pm.GEV`. This was replaced with `pm.CustomDist` wrapping a PyTensor-native GEV logp function. Reason: `pm.GEV` availability across PyMC versions is not guaranteed; custom implementation is portable.

### 2. LP3 logp — PyTensor, not `scipy.stats`
The original plan proposed `scipy.stats.pearson3.logpdf` directly inside `pm.CustomDist`. This breaks PyTensor's computation graph (no analytical gradients → NUTS cannot compute HMC steps). The LP3 logp was re-implemented from scratch using `pytensor.tensor` and `pt.special.gammaln`.

### 3. TCEV — `pm.Potential` ordering constraint, not `pm.Mixture`
The original plan proposed `pm.Mixture`. The final implementation uses a manual logsumexp mixture likelihood inside `pm.CustomDist`, with `pm.Potential("order_constraint", ...)` enforcing `mu1 < mu2` to prevent label switching. The `pm.Potential` assigns `-inf` log-probability to any draw where the constraint is violated.

### 4. `target_accept` raised to 0.95 for LP3 and TCEV
Originally 0.9. Raised to 0.95 after observing high divergence counts during sampling.

### 5. FLIKE emulator added (not in original plan)
Modules `stats/lh_moments.py`, `stats/bootstrap.py`, `gev/fit_lh.py`, `lp3/fit_lh.py`, `flike.py`, `plots_lh.py`, notebook `06_flike_emulator.ipynb`, and the `preprocessing/` subpackage were all added beyond the original scope.

### 6. Plotting conventions locked in a SKILL file
`SKILLS/plotting/pyfloodextremes-plotting-SKILL.md` defines the canonical Australian/ARR plotting conventions. See that file for all plot code references. Key choices:
- `probscale` probability scale, not log ARI axis
- AEP (%) not ARI (years) — ARR 2019 convention
- X axis: left = frequent, right = rare; limits `[63, 0.1]`
- Cunnane plotting positions, not Weibull
- 94% HDI uncertainty bands
- WRM Blue `#1e4164` (GEV), WRM Teal `#00928f` (LP3), WRM Green `#8dc63f` (TCEV), Charcoal `#485253` (observed)

---

## Known Issues

### Critical — Notebook 06 (FLIKE Emulator)
The LP3 LH-moment solver (`scipy.optimize.root`) was failing with `RuntimeError: Failed to fit model for any shift`. It was patched to use `scipy.optimize.least_squares`. Whether the patched version runs successfully in `06_flike_emulator.ipynb` is **unconfirmed** — the session timed out before re-execution. The notebook should be re-run and inspected before treating it as valid training material.

### Critical — Bootstrap Confidence Limits in Notebook 06 (Suspected Bug)
When the GEV section of notebook 06 runs, the reported 5th/95th percentile bootstrap limits appear far below the expected quantile values (e.g., at 1% AEP: expected = 79.0 m3/s but 5% limit = 18.7, 95% limit = 23.1). Both limits sit well below the expected value, which is physically impossible — they should bracket it. This is almost certainly a bug in how bootstrap quantile percentiles are being computed or reported.

### High — TCEV Convergence (2020 divergences, unvalidated)
Notebook 03 shows 2020 divergences after tuning. The ordering constraint is in place but whether the sampler actually converges cleanly on this dataset has not been confirmed by systematic trace plot inspection. The constraint suppresses label switching but does not guarantee good geometry for NUTS.

### High — Notebook 03 "Scientific Narrative" Cell is Empty
The final markdown cell in `03_tcev_demo.ipynb` is titled "## Scientific Narrative" but has no content. This was intended as the key interpretive section explaining what the component separation plot tells us about the 2021 event and the case for the TCEV model.

### Medium — GEV/LP3 Divergence Counts in Notebooks 01, 02
Notebook 01 shows 18 divergences, notebook 02 shows 77. Neither is addressed in the notebook markdown. Readers will see the sampler warnings and have no guidance on whether to trust the results or how to interpret divergences.

### Medium — `gev_cdf_np` scalar branch potential shape bug
In `tcev/plots.py`, the `gev_cdf_np` function contains `if abs(xi) < eps: cdf = np.exp(-np.exp(-z))`. When `xi` is near zero for a vector input, this scalar assignment may produce incorrect shapes. Needs review.

### Low — No unit tests
`pytest tests/` collects 0 items. No tests exist anywhere in the project.

### Low — HTML exports unconfirmed
HTML exports of notebooks 01–05 may or may not exist. Git status shows some `.html` files as untracked. Notebook 06 HTML almost certainly does not exist.

### Low — Bootstrap vs HDI mismatch in comparison
FLIKE bootstrap returns 5th/95th percentile limits. Bayesian modules return 94% HDI. These are not directly comparable. No decision has been made on alignment.

---

## Outstanding Work (Priority Order)

1. **Re-run and verify notebook 06** — confirm LP3 LH-moment solver works; fix bootstrap limits bug.
2. **Write the TCEV scientific narrative** — fill the empty cell in notebook 03 with interpretation of the component separation plot, what it says about 2021, and the case for TCEV vs GEV.
3. **Address divergences in narrative** — add markdown cells in notebooks 01, 02, 03 explaining what divergences mean and whether the current counts affect result validity.
4. **Interpret posterior summaries** — add explanation of r_hat, ess_bulk, ess_tail, mcse to each notebook.
5. **Add foundational concepts** — notebooks currently assume knowledge of AEP, return period, Bayesian inference, NUTS, HDI. Add introductory cells or a standalone `00_concepts.ipynb`.
6. **Validate MGBT** against R reference output at `E:\GitHub\MGBT_1.0.7`.
7. **Write unit tests** — at minimum: logp functions return correct scalar values; plotting functions run without error.
8. **Export HTML snapshots** — `jupyter nbconvert --to html notebooks/*.ipynb`.
9. **Expand README** — add worked example, result table, and conceptual framing of the scientific question.

---

## Scientific Context (Summary)

- **Dataset**: `data/AMS.csv` — 55-year AMS (1970–2024). 2021 event (121.9 m3/s) is nearly double the next highest (48.3 m3/s in 2022). This outlier is the scientific thread connecting all three models.
- **Core question**: *How does distribution choice affect design flood estimates when the record contains a potentially extraordinary event?* (Target: HWRS/FMA conference papers)
- **GEV**: Single-population model. The 2021 event inflates the shape parameter (xi ≈ 0.31), implying a heavy tail across all return periods.
- **LP3**: ARR default. Fits in log-space. Skewness posterior ≈ 0.45 — moderate positive skew.
- **TCEV**: Mixture of two GEV populations. Component 2 (`w ~ Beta(1,10)`) models extraordinary floods. The `w` posterior and component separation plot should assign high probability to 2021 belonging to Component 2.
- **MGBT**: ARR 2019 preprocessing step to identify Potentially Influential Low Flows (PILFs) before fitting. Our dataset has no natural low outliers.
- **FLIKE emulator**: Frequentist alternative to the Bayesian modules. LH-moments (shift eta=0–4) up-weight upper-tail observations; parametric bootstrap provides uncertainty limits. Intended for comparison against Bayesian estimates in the conference paper.

---

## Environment Notes

- Python 3.13.7, managed by `uv`
- Dedicated Jupyter kernel: `pyfloodextremes` (installed from `.venv`)
- PyMC version requires `pm.CustomDist` for GEV and LP3 — `pm.GEV` is NOT used
- `scipy.stats.genextreme` uses negated xi convention: pass `c=-xi` to all `scipy.stats.genextreme` calls
- Activate: `.venv\Scripts\activate` (Windows PowerShell)
- All shell commands use PowerShell syntax (`;` not `&&` for sequential commands)
