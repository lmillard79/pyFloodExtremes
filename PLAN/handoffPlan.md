Here is the full handoff document.

---

**pyFloodExtremes -- Claude Code Handoff Document**

---

**Project overview**

`pyFloodExtremes` is a Python package for Bayesian flood frequency analysis built on `pyextremes` and `PyMC`. It implements three distribution families -- GEV, LP3, and TCEV (two-component extreme value) -- using MCMC sampling via PyMC with ArviZ diagnostics. The project is a learning and experimentation platform with a secondary goal of producing material for HWRS and FMA conference papers on Australian flood frequency practice.

---

**Repository**

- GitHub: `https://github.com/lmillard79/pyFloodExtremes`
- Local: `E:\GitHub\pyFloodExtremes`
- Branch: `main`

---

**Environment**

- OS: Windows, PowerShell
- Python: 3.13.7
- Package manager: `uv`

Activate the environment:
```bash
cd E:\GitHub\pyFloodExtremes
.venv\Scripts\activate
```

Run tests:
```bash
pytest tests/
```

---

**Dependency stack**

| Library | Role |
|---|---|
| `pyextremes` | Block maxima extraction only -- not used for fitting |
| `pymc` | All Bayesian model fitting |
| `arviz` | Posterior diagnostics, trace and corner plots |
| `matplotlib` | Return period and comparison plots |
| `pandas` | Data handling |
| `numpy` | Numerical operations |
| `scipy` | LP3 distribution via `pearson3` |
| `jupyter` | Example notebooks |

---

**Package structure**

```
pyFloodExtremes/
  src/
    flood_ffa/
      __init__.py
      gev/
        __init__.py
        fit.py          # TO BUILD
        plots.py        # TO BUILD
      lp3/
        __init__.py
        fit.py          # TO BUILD
        plots.py        # TO BUILD
      tcev/
        __init__.py     # TO CREATE
        fit.py          # TO BUILD
        plots.py        # TO BUILD
      data/
        __init__.py
        bom.py          # DONE -- data loader
      compare.py        # TO BUILD
  notebooks/
    01_gev_demo.ipynb   # TO BUILD
    02_lp3_demo.ipynb   # TO BUILD
    03_tcev_demo.ipynb  # TO BUILD
    04_comparison.ipynb # TO BUILD
  data/
    AMS.csv             # DONE -- 55 year gauge record
  tests/
    __init__.py
  pyproject.toml        # DONE
  README.md             # TO UPDATE
```

---

**Example dataset**

`data/AMS.csv` contains 55 years of annual maximum flows (1970--2024) with columns:

- `year` -- index
- `water_level_mAHD` -- annual maximum water level
- `flow_m3s` -- annual maximum flow in m3/s

Key feature: 2021 is a major outlier at 121.9 m3/s, nearly double the next highest value (48.3 m3/s in 2022). This is the primary scientific motivation for the TCEV model.

Load the data:
```python
from flood_ffa.data.bom import load_ams, get_flow_series
df = load_ams("data/AMS.csv")
flows = get_flow_series(df)
```

---

**Data loader -- already built**

`src/flood_ffa/data/bom.py` provides:

- `load_ams(filepath)` -- returns DataFrame indexed by year
- `get_flow_series(df)` -- returns `pd.Series` of flows in m3/s

---

**Build sequence**

Work through these modules in order. Each module must be tested and committed before moving to the next.

---

**Module 1: `src/flood_ffa/gev/fit.py`**

Single-population GEV fitted via PyMC.

Interface:
```python
def fit_gev(flows: pd.Series, draws: int = 2000, tune: int = 1000) -> az.InferenceData:
```

PyMC model:
```python
with pm.Model() as model:
    mu = pm.Normal("mu", mu=flows.mean(), sigma=flows.std())
    sigma = pm.HalfNormal("sigma", sigma=flows.std())
    xi = pm.Normal("xi", mu=0, sigma=0.2)  # weakly informative shape prior
    obs = pm.GEV("obs", mu=mu, sigma=sigma, xi=xi, observed=flows.values)
    idata = pm.sample(draws, tune=tune, return_inferencedata=True)
return idata
```

Notes:
- Prior on `xi` centred at zero -- reflects prior belief that shape is near-Gumbel
- `sigma=0.2` on xi is intentionally tight -- floods rarely have extreme shape parameters
- Document all prior choices with comments

---

**Module 2: `src/flood_ffa/gev/plots.py`**

Functions:
- `plot_trace(idata)` -- ArviZ trace plot for mu, sigma, xi
- `plot_corner(idata)` -- ArviZ pair plot showing posterior correlations
- `plot_return_levels(idata, flows, return_periods)` -- return level curve with 94% HDI uncertainty band

Return period curve notes:
- X axis: return period in years (log scale)
- Y axis: flow in m3/s
- Plot observed data using Weibull plotting positions
- Overlay posterior median and 94% HDI band

---

**Module 3: `src/flood_ffa/lp3/fit.py`**

LP3 is the ARR default distribution. Fit in log-space using `scipy.stats.pearson3` wrapped in `pm.CustomDist`.

Interface:
```python
def fit_lp3(flows: pd.Series, draws: int = 2000, tune: int = 1000) -> az.InferenceData:
```

PyMC model structure:
```python
log_flows = np.log(flows.values)

def lp3_logp(value, mu, sigma, skew):
    return pm.math.sum(scipy.stats.pearson3.logpdf(value, skew, loc=mu, scale=sigma))

with pm.Model() as model:
    mu = pm.Normal("mu", mu=log_flows.mean(), sigma=log_flows.std())
    sigma = pm.HalfNormal("sigma", sigma=log_flows.std())
    skew = pm.Normal("skew", mu=0, sigma=0.5)  # skewness -- ARR suggests near-zero for many AU catchments
    obs = pm.CustomDist("obs", mu, sigma, skew, logp=lp3_logp, observed=log_flows)
    idata = pm.sample(draws, tune=tune, return_inferencedata=True)
return idata
```

Notes:
- All fitting in log-space -- back-transform for return level plots
- Skewness prior centred at zero with moderate variance

---

**Module 4: `src/flood_ffa/lp3/plots.py`**

Same plot suite as GEV:
- `plot_trace(idata)`
- `plot_corner(idata)`
- `plot_return_levels(idata, flows, return_periods)`

Return level back-transformation:
- Sample return levels in log-space from posterior
- Exponentiate before plotting
- Units remain m3/s throughout

---

**Module 5: `src/flood_ffa/tcev/fit.py`**

Two-component extreme value model. This is the scientific centrepiece of the project.

Motivation: The 2021 flood (121.9 m3/s) is a strong candidate for a physically distinct flood-generating mechanism. A single GEV will either inflate the shape parameter to accommodate it or underfit the upper tail. TCEV models the AMS as a mixture of two GEV populations.

Interface:
```python
def fit_tcev(flows: pd.Series, draws: int = 2000, tune: int = 1000) -> az.InferenceData:
```

PyMC model:
```python
with pm.Model() as model:
    # Mixing weight -- prior favours extraordinary floods being rare
    w = pm.Beta("w", alpha=1, beta=10)

    # Component 1 -- ordinary floods
    mu1 = pm.Normal("mu1", mu=flows.mean(), sigma=flows.std())
    sigma1 = pm.HalfNormal("sigma1", sigma=flows.std())
    xi1 = pm.Normal("xi1", mu=0, sigma=0.2)

    # Component 2 -- extraordinary floods
    # Prior centres mu2 above component 1
    mu2 = pm.Normal("mu2", mu=flows.quantile(0.9), sigma=flows.std())
    sigma2 = pm.HalfNormal("sigma2", sigma=flows.std())
    xi2 = pm.Normal("xi2", mu=0, sigma=0.2)

    like = pm.Mixture(
        "like",
        w=pm.math.stack([1 - w, w]),
        comp_dists=[
            pm.GEV.dist(mu=mu1, sigma=sigma1, xi=xi1),
            pm.GEV.dist(mu=mu2, sigma=sigma2, xi=xi2),
        ],
        observed=flows.values,
    )
    idata = pm.sample(draws, tune=tune, return_inferencedata=True, target_accept=0.9)
return idata
```

Notes:
- `target_accept=0.9` -- mixture models need higher acceptance rate for stable sampling
- The `w` posterior tells you the probability each observation belongs to component 2 -- scientifically interesting
- Label switching is a known issue with mixture models -- monitor via trace plots

---

**Module 6: `src/flood_ffa/tcev/plots.py`**

Additional plots beyond the standard suite:

- `plot_trace(idata)` -- trace for all 7 parameters
- `plot_corner(idata)` -- pair plot
- `plot_return_levels(idata, flows, return_periods)` -- mixture return level curve
- `plot_component_separation(idata, flows)` -- posterior probability each observation belongs to component 2, plotted against year -- this will highlight 2021

---

**Module 7: `src/flood_ffa/compare.py`**

Side-by-side return level comparison across all three models.

Interface:
```python
def plot_comparison(
    gev_idata: az.InferenceData,
    lp3_idata: az.InferenceData,
    tcev_idata: az.InferenceData,
    flows: pd.Series,
    return_periods: list[float],
) -> matplotlib.figure.Figure:
```

Plot design:
- Single figure, three overlaid return level curves
- Each curve shows posterior median and 94% HDI band
- Observed data plotted as points using Weibull plotting positions
- Legend clearly labels GEV, LP3, TCEV
- Highlight divergence in the upper tail (100 year, 2000 year return periods)

---

**Notebooks**

Each notebook should be self-contained and runnable top to bottom.

`01_gev_demo.ipynb`
- Load AMS data
- Fit GEV
- Plot trace, corner, return levels
- Summarise posterior parameters

`02_lp3_demo.ipynb`
- Load AMS data
- Fit LP3
- Plot trace, corner, return levels
- Compare to GEV informally

`03_tcev_demo.ipynb`
- Load AMS data
- Fit TCEV
- Plot all diagnostics including component separation
- Discuss 2021 outlier in context of posterior

`04_comparison.ipynb`
- Load AMS data
- Fit all three models
- Plot comparison figure
- Table of return levels at 10, 20, 50, 100, 200, 2000 year return periods with uncertainty

---

**Design principles**

- PyMC for all fitting -- do not use pyextremes Bayesian backend
- Consistent interface across all three modules -- accept `pd.Series`, return `InferenceData`
- Weakly informative priors throughout -- all prior choices documented with comments explaining the hydrological rationale
- Australian flood practice context in all docstrings -- ARR references where relevant, m3/s units, AEP framing
- Commit after each module is tested and working

---

**Git workflow**

```bash
git add .
git commit -m "feat: <description>"
git push origin main
```

Suggested commit messages:
- `feat: add GEV fit module`
- `feat: add GEV plot module`
- `feat: add LP3 fit module`
- `feat: add LP3 plot module`
- `feat: add TCEV fit module`
- `feat: add TCEV plot module`
- `feat: add comparison module`
- `feat: add example notebooks`

---

**Known issues to watch for**

- Label switching in TCEV -- if component 1 and component 2 swap identity during sampling, trace plots will show bimodal posteriors. May need an ordering constraint on mu1 < mu2.
- PyMC GEV availability -- confirm `pm.GEV` exists in the installed PyMC version before writing fit modules. If not available, use `pm.CustomDist` wrapping `scipy.stats.genextreme`.
- LP3 CustomDist -- the `logp` function must return a scalar, not a vector. Use `pm.math.sum()`.

---

**Scientific narrative for HWRS/FMA**

The 2021 flood in this record is the thread connecting all three models. The comparison notebook should be written with this question in mind:

*How does the choice of frequency distribution affect design flood estimates when the record contains a potentially extraordinary event?*

That framing connects directly to the non-stationarity and climate change work already underway.