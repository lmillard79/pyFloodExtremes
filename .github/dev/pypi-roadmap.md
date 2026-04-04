# PyPI Publication Roadmap — pyFloodExtremes

This document tracks the steps required to publish `pyfloodextremes` to PyPI.
Current version: **0.1.0** (pre-release, not yet published).

---

## Phase 1 — Package housekeeping
*Make the package installable and correctly described.*

- [ ] **1.1 Fix `pyproject.toml`**

  Remove `pyextremes` and `jupyter` from runtime `dependencies` — they are not imported by `src/` code. Move `jupyter` to `[dependency-groups] dev`.

  Add author email (required for PyPI):
  ```toml
  authors = [{ name = "Lindsay Millard", email = "your@email.com" }]
  ```

  Add project URLs (required for a useful PyPI page):
  ```toml
  [project.urls]
  Homepage = "https://github.com/lmillard79/pyFloodExtremes"
  Repository = "https://github.com/lmillard79/pyFloodExtremes"
  Documentation = "https://github.com/lmillard79/pyFloodExtremes/tree/main/docs/theory"
  ```

  Add classifiers (helps discoverability):
  ```toml
  classifiers = [
      "Programming Language :: Python :: 3",
      "License :: OSI Approved :: MIT License",
      "Topic :: Scientific/Engineering :: Hydrology",
      "Intended Audience :: Science/Research",
      "Operating System :: OS Independent",
  ]
  ```

- [ ] **1.2 Populate `src/flood_ffa/__init__.py` with the public API**

  Right now the top-level `__init__.py` only suppresses a warning. It should expose the primary entry points so users can write `from flood_ffa import fit_gev` rather than knowing the internal submodule layout:

  ```python
  from flood_ffa.gev.fit import fit_gev
  from flood_ffa.lp3.fit import fit_lp3
  from flood_ffa.tcev.fit import fit_tcev
  from flood_ffa.flike import FLIKE
  from flood_ffa.preprocessing.mgbt import detect_low_outliers
  from flood_ffa.data.bom import load_ams, get_flow_series
  from flood_ffa.compare import plot_comparison
  ```

- [ ] **1.3 Set `stats/` subpackage `__init__.py`**

  `src/flood_ffa/stats/` has no `__init__.py` — check if one is needed (it is if anything imports from `flood_ffa.stats` directly).

- [ ] **1.4 Confirm `LICENSE` file exists and matches `pyproject.toml`**

  The pyproject.toml says `license = { text = "MIT" }`. Verify `LICENSE` (or `LICENSE.md`) is in the repo root with the full MIT text and Lindsay's name.

---

## Phase 2 — Minimal test coverage
*PyPI does not require tests, but a package used for engineering design decisions should have them.*

- [ ] **2.1 Smoke tests for core fit functions**

  In `tests/test_fitting.py`, at minimum:
  - Generate 30 synthetic GEV samples → call `fit_gev` → assert `idata` has expected variables (`mu`, `sigma`, `xi`)
  - Same for `fit_lp3` (variables: `mu_Y`, `sigma_Y`, `gamma`)
  - Assert posterior median 1% AEP quantile is within a physically plausible range

- [ ] **2.2 Unit tests for LH-moments engine**

  In `tests/test_lh_moments.py`:
  - Test PWM computation against a known small sample
  - Test LH-moment fitting recovers known GEV parameters within tolerance
  - Test bootstrap CI brackets the fitted quantile

- [ ] **2.3 MGBT smoke test**

  In `tests/test_mgbt.py`:
  - Feed a series with one obvious low outlier → assert it is flagged
  - Feed a clean series → assert `k_low == 0`

- [ ] **2.4 Wire up CI (GitHub Actions)**

  Create `.github/workflows/test.yml` that runs `pytest` on push to `main` and on pull requests. This is what other developers will look for before trusting the package.

  Minimal workflow:
  ```yaml
  name: tests
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - uses: astral-sh/setup-uv@v4
        - run: uv sync
        - run: uv run pytest tests/
  ```

---

## Phase 3 — Versioning and changelog
*Establishes the release discipline expected of a published package.*

- [ ] **3.1 Adopt semantic versioning explicitly**

  Current version `0.1.0` is appropriate for a first public release (pre-stable).
  Convention going forward:
  - `0.x.0` — new features or breaking API changes while pre-stable
  - `0.x.y` — bug fixes
  - `1.0.0` — first stable, API-locked release

- [ ] **3.2 Create `CHANGELOG.md`**

  Document what is in `0.1.0`. Future users (and your future self) will look here when upgrading. Keep it brief — what changed, what was fixed, what was added.

---

## Phase 4 — Build and publish
*The actual release steps.*

- [ ] **4.1 Check the package name is available**

  ```bash
  pip index versions pyfloodextremes
  ```
  If it returns "no matching distribution found", the name is free on PyPI.

- [ ] **4.2 Install build tools**

  ```bash
  uv add --dev build twine
  ```

- [ ] **4.3 Build the distribution**

  ```bash
  uv run python -m build
  ```
  This creates two files in `dist/`:
  - `pyfloodextremes-0.1.0.tar.gz` (source distribution)
  - `pyfloodextremes-0.1.0-py3-none-any.whl` (wheel)

- [ ] **4.4 Test on TestPyPI first**

  Create a free account at https://test.pypi.org if you don't have one.
  Generate an API token and save it.

  ```bash
  uv run twine upload --repository testpypi dist/*
  # then test the install:
  pip install --index-url https://test.pypi.org/simple/ pyfloodextremes
  python -c "from flood_ffa import fit_gev; print('OK')"
  ```

- [ ] **4.5 Publish to PyPI**

  Create an account at https://pypi.org, generate an API token.

  ```bash
  uv run twine upload dist/*
  ```

  After this, anyone can install with:
  ```bash
  pip install pyfloodextremes
  ```

---

## Phase 5 — Post-release polish
*Nice to have, not blocking.*

- [ ] **5.1 Add a `notebooks/00_foundations.ipynb`** — standalone concepts notebook covering AMS, AEP/ARI, EVT, and all four inference methods. Source material already written in `docs/theory/`.

- [ ] **5.2 Add nbviewer badge to README for notebook 06** — the link is in the table but needs a working executed notebook pushed to GitHub first.

- [ ] **5.3 Consider a DOI via Zenodo** — if citing in the HWRS/FMA papers, a Zenodo DOI makes pyFloodExtremes formally citable. Zenodo connects directly to GitHub releases.

- [ ] **5.4 Add `SKILLS/` to `.gitignore`** — these are internal working files, not relevant to package users.

---

## Current blockers

None — the package is buildable today. Phase 1 changes to `pyproject.toml` and `__init__.py` are the only things standing between the current state and a publishable `0.1.0`.

The recommended order is: **Phase 1 → Phase 4.1-4.4 (TestPyPI) → Phase 2 → Phase 4.5 (real PyPI)**.
Adding tests before the real release is strongly recommended given the engineering use case.
