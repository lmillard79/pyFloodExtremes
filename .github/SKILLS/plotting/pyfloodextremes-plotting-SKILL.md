---
name: pyfloodextremes-plotting
description: Apply correct Australian flood frequency analysis plotting conventions to all return period and probability plots in the pyFloodExtremes project. Use this skill whenever writing or reviewing any plot function in flood_ffa/gev/plots.py, flood_ffa/lp3/plots.py, flood_ffa/tcev/plots.py, or flood_ffa/compare.py. Also trigger when the user mentions AEP, return period plots, probability scale, plotting positions, or frequency curves.
---

# pyFloodExtremes Plotting Skill

This skill defines the correct plotting conventions for all flood frequency
analysis figures in the pyFloodExtremes project. These conventions follow
Australian practice (ARR 2019) and the user's explicit preferences.

---

## Core Conventions

### Probability Scale -- Not Log Scale

All return period / frequency plots MUST use a probability scale on the X axis.
Do NOT use a log-scale return period axis (e.g. log(ARI years)).

The probability scale linearises the fitted distribution:
- GEV / Gumbel: use Gumbel reduced variate transform
- LP3: use normal probability scale (probit transform)
- TCEV: use Gumbel reduced variate (matches GEV component)
- Let the distribution determine which transform is applied

The `probscale` library provides a matplotlib scale for this:

```python
import probscale  # pip install probscale
```

Register the scale and apply to the X axis:

```python
ax.set_xscale("prob")  # probscale registers this scale automatically on import
```

### Axis Orientation

- **Y axis**: Flow (m³/s) -- linear scale
- **X axis**: Annual Exceedance Probability (AEP) -- probability scale
- X axis direction: LEFT = high AEP (frequent), RIGHT = low AEP (rare)
  - i.e. 50% on the left, 0.2% on the right

### AEP Not ARI

ALWAYS use Annual Exceedance Probability (AEP) expressed as a percentage.
NEVER use Average Recurrence Interval (ARI) in years as the primary axis label.

Correct:   "Annual Exceedance Probability (%)"
Incorrect: "Return Period (years)"
Incorrect: "ARI (years)"

---

## AEP Axis Configuration

### Tick Marks

Always use these AEP values as X axis ticks (in percent):

```python
AEP_TICKS = [50, 20, 10, 5, 2, 1, 0.5, 0.2]
```

Format tick labels as percentages:

```python
ax.set_xticks(AEP_TICKS)
ax.set_xticklabels([f"{p}%" for p in AEP_TICKS])
```

### Axis Limits

Set X axis limits slightly beyond the outermost ticks:

```python
ax.set_xlim([63, 0.1])  # probscale expects probability values 0-100
```

Note: probscale takes values in the range 0--100 (percent), not 0--1.
Pass AEP values as percentages throughout.

### Axis Label

```python
ax.set_xlabel("Annual Exceedance Probability (%)")
```

---

## Plotting Positions for Observed Data

Use **Cunnane plotting positions**:

```
p_i = (m - 0.4) / (n + 0.2)
```

Where:
- `m` = rank of observation (1 = smallest)
- `n` = total number of observations
- Result is a probability in [0, 1] -- multiply by 100 for percent

```python
import numpy as np

def cunnane_plotting_positions(flows: np.ndarray) -> np.ndarray:
    """
    Compute Cunnane plotting positions for observed annual maxima.

    Parameters
    ----------
    flows : np.ndarray
        Annual maximum flows, unsorted.

    Returns
    -------
    np.ndarray
        AEP values in percent (0--100), sorted ascending by flow.
    """
    n = len(flows)
    ranks = np.argsort(np.argsort(flows)) + 1  # ranks 1..n
    aep = (ranks - 0.4) / (n + 0.2) * 100      # convert to percent
    return aep
```

Plot observed data:

```python
aep_obs = cunnane_plotting_positions(flows.values)
ax.scatter(aep_obs, np.sort(flows.values), 
           color='#485253', zorder=5, label='Observed AMS', s=30)
```

---

## Return Level Curve from Posterior

Convert posterior samples to return levels on the AEP grid.

### AEP Grid

```python
AEP_GRID = np.array([50, 20, 10, 5, 2, 1, 0.5, 0.2])  # percent
```

For plotting a smooth curve, use a finer grid:

```python
AEP_FINE = np.logspace(np.log10(0.2), np.log10(63), 200)  # percent
```

### GEV Return Level Calculation

For each posterior sample (mu, sigma, xi), compute return level at AEP p%:

```python
from scipy.stats import genextreme

def gev_return_level(mu, sigma, xi, aep_pct):
    """
    Compute GEV return level for a given AEP.

    Parameters
    ----------
    mu, sigma, xi : float
        GEV location, scale, shape parameters.
    aep_pct : float or np.ndarray
        AEP in percent (e.g. 1.0 for 1% AEP).

    Returns
    -------
    float or np.ndarray
        Return level in same units as mu (m³/s).
    """
    p = aep_pct / 100.0  # convert to probability
    # scipy genextreme uses shape convention: sign of xi is negated vs standard
    return genextreme.ppf(1 - p, c=-xi, loc=mu, scale=sigma)
```

### LP3 Return Level Calculation

Fit and predict in log-space, then exponentiate:

```python
from scipy.stats import pearson3

def lp3_return_level(mu, sigma, skew, aep_pct):
    """
    Compute LP3 return level for a given AEP.
    Fitting is in log-space; output is back-transformed to m³/s.
    """
    p = aep_pct / 100.0
    log_rl = pearson3.ppf(1 - p, skew, loc=mu, scale=sigma)
    return np.exp(log_rl)
```

### Posterior Uncertainty Band

Extract posterior samples from InferenceData and compute HDI:

```python
import arviz as az
import numpy as np

def compute_return_level_hdi(idata, dist, aep_grid, hdi_prob=0.94):
    """
    Compute posterior median and HDI band for return levels.

    Parameters
    ----------
    idata : az.InferenceData
        Posterior samples from PyMC fit.
    dist : str
        One of 'gev', 'lp3', 'tcev'.
    aep_grid : np.ndarray
        AEP values in percent.
    hdi_prob : float
        HDI probability mass (default 0.94).

    Returns
    -------
    median : np.ndarray
        Posterior median return level at each AEP.
    lower : np.ndarray
        Lower HDI bound.
    upper : np.ndarray
        Upper HDI bound.
    """
    posterior = idata.posterior
    
    if dist == 'gev':
        mu    = posterior['mu'].values.flatten()
        sigma = posterior['sigma'].values.flatten()
        xi    = posterior['xi'].values.flatten()
        rl_samples = np.array([
            gev_return_level(mu[i], sigma[i], xi[i], aep_grid)
            for i in range(len(mu))
        ])
    elif dist == 'lp3':
        mu    = posterior['mu'].values.flatten()
        sigma = posterior['sigma'].values.flatten()
        skew  = posterior['skew'].values.flatten()
        rl_samples = np.array([
            lp3_return_level(mu[i], sigma[i], skew[i], aep_grid)
            for i in range(len(mu))
        ])

    median = np.median(rl_samples, axis=0)
    hdi    = az.hdi(rl_samples, hdi_prob=hdi_prob)
    return median, hdi[:, 0], hdi[:, 1]
```

---

## Standard Return Period Plot

Full reference implementation:

```python
import matplotlib.pyplot as plt
import probscale
import numpy as np

def plot_return_levels(idata, flows, dist='gev', hdi_prob=0.94,
                       title=None, ax=None):
    """
    Plot flood frequency curve on probability scale.

    Parameters
    ----------
    idata : az.InferenceData
        Posterior from PyMC fit.
    flows : pd.Series
        Observed annual maximum flows in m³/s.
    dist : str
        'gev', 'lp3', or 'tcev'.
    hdi_prob : float
        Posterior HDI probability mass (default 0.94).
    title : str, optional
        Figure title.
    ax : matplotlib Axes, optional
        If None, a new figure is created.

    Returns
    -------
    fig, ax
    """
    import probscale  # registers 'prob' scale

    AEP_TICKS = [50, 20, 10, 5, 2, 1, 0.5, 0.2]
    AEP_FINE  = np.logspace(np.log10(0.2), np.log10(63), 300)

    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
    else:
        fig = ax.get_figure()

    # -- Posterior return level curve --
    median, lower, upper = compute_return_level_hdi(
        idata, dist, AEP_FINE, hdi_prob=hdi_prob
    )

    label = dist.upper()
    ax.plot(AEP_FINE, median, color='#1e4164', lw=1.5, label=f'{label} posterior median')
    ax.fill_between(AEP_FINE, lower, upper, alpha=0.25, color='#1e4164',
                    label=f'{label} {int(hdi_prob*100)}% HDI')

    # -- Observed data --
    aep_obs = cunnane_plotting_positions(flows.values)
    ax.scatter(aep_obs, np.sort(flows.values),
               color='#485253', zorder=5, s=30, label='Observed AMS')

    # -- Axes --
    ax.set_xscale('prob')
    ax.set_xlim([63, 0.1])
    ax.set_xticks(AEP_TICKS)
    ax.set_xticklabels([f'{p}%' for p in AEP_TICKS])
    ax.set_xlabel('Annual Exceedance Probability (%)')
    ax.set_ylabel('Flow (m³/s)')
    ax.set_title(title or f'{label} Flood Frequency Curve')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='0.7')
    ax.legend()
    fig.tight_layout()

    return fig, ax
```

---

## Comparison Plot (GEV vs LP3 vs TCEV)

When overlaying multiple distributions on a single axes:

```python
DIST_COLOURS = {
    'gev':  '#1e4164',  # WRM Blue
    'lp3':  '#00928f',  # WRM Teal
    'tcev': '#8dc63f',  # WRM Green
}
```

Each distribution gets its own colour. The observed data is always plotted
last in Charcoal (`#485253`) so it sits visually above the fitted curves.

---

## Dependency

`probscale` must be added to `pyproject.toml`:

```toml
dependencies = [
    ...
    "probscale",
]
```

Install via:

```bash
uv add probscale
```

---

## Checklist Before Delivering Any Frequency Plot

- [ ] X axis uses `probscale` probability scale -- NOT log scale
- [ ] X axis label is "Annual Exceedance Probability (%)"
- [ ] X axis ticks are 50%, 20%, 10%, 5%, 2%, 1%, 0.5%, 0.2%
- [ ] X axis direction is left (frequent) to right (rare)
- [ ] Y axis is Flow (m³/s) on linear scale
- [ ] Observed data plotted using Cunnane plotting positions
- [ ] Uncertainty shown as 94% HDI band -- not confidence interval
- [ ] Legend present and clearly labels each series
- [ ] `probscale` listed in `pyproject.toml` dependencies
- [ ] No reference to ARI or return period (years) as primary axis

---

## Common Issues

| Issue | Fix |
|---|---|
| `probscale` not found | `uv add probscale` then restart kernel |
| X axis plots left-to-right in wrong direction | Set `ax.set_xlim([63, 0.1])` -- high AEP on left |
| AEP values outside 0--100 range | probscale expects percent, not probability -- multiply by 100 |
| scipy GEV sign convention | `genextreme.ppf` uses `-xi` -- see `gev_return_level` above |
| LP3 back-transform missing | Always `np.exp()` LP3 return levels before plotting |
| HDI not available | Use `arviz>=0.15` -- `az.hdi()` accepts 2D arrays directly |
