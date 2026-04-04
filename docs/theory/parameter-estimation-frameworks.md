# Parameter Estimation Frameworks in Flood Frequency Analysis

This document covers how the key parameters of flood frequency distributions are defined, estimated, and refined within the broader statistical frameworks used in practice.

---

## Key Parameters in Common Distributions

### GEV and LP3

Both distributions used in `pyFloodExtremes` have three parameters:

**Generalised Extreme Value (GEV)**

| Parameter | Symbol | Effect |
|---|---|---|
| Location | $\mu$ | Shifts the distribution — approximately the median AMS value |
| Scale | $\sigma > 0$ | Controls spread |
| Shape | $\xi$ | Controls tail weight — the dominant parameter for rare event extrapolation |

**Log-Pearson Type 3 (LP3)** — operates on log-flows $Y = \ln(Q)$:

| Parameter | Symbol | Effect |
|---|---|---|
| Location | $\mu_Y$ | Mean in log-space — related to median flow by $e^{\mu_Y}$ |
| Scale | $\sigma_Y > 0$ | Spread in log-space |
| Skewness | $\gamma$ | Tail asymmetry — positive means upper tail is heavier |

The skewness parameter $\gamma$ has an outsized and **non-linear** influence on rare flood quantiles. Its uncertainty propagates strongly into design estimates, particularly at return periods beyond the record length. This is why ARR recommends weighting at-site skewness with regional information for short records.

---

## Expected Parameter vs Expected Probability Quantiles

The Bayesian framework produces two types of design quantile that serve different purposes:

**Expected parameter quantile**
The return level computed at the *mean* (or *mode*) of the posterior parameter distribution. This minimises bias in the *magnitude* of the design flood and is the standard output for engineering design.

**Expected probability quantile**
The return level obtained by averaging over the full posterior parameter distribution. This minimises bias in the *exceedance probability* — meaning the probability statement attached to the design flood is more accurate. Important when the output is used in probabilistic risk assessments (e.g., expected annual damages).

`pyFloodExtremes` reports the **posterior median** return level, which is a robust central estimate that sits between these two and is less sensitive to skewed posteriors than the mean.

---

## Regional Flood Frequency Estimation (RFFE)

When at-site records are too short or a site is ungauged, regional information is incorporated:

### Parameter Regression Technique (PRT)

The distribution parameters (e.g., mean, standard deviation, and skewness of log-flows for LP3) are regressed against catchment characteristics such as:
- Catchment area
- Design rainfall intensity (e.g., 2-hour 50% AEP rainfall)
- Fraction impervious

This regression is typically performed using **Generalised Least Squares (GLS)**, which separates the underlying model error from the time-sampling error in each station's parameter estimates.

### Regional Bayesian Models

More sophisticated approaches use regional data to construct a **prior distribution** for the target site's parameters. The prior is built from "pseudo-target site parameters" derived from nearby hydrologically similar sites, rescaled using the target site's index flood. The target site's own data then updates this prior via Bayes' Theorem.

Key advantage over the traditional Index Flood model: rather than assuming all sites in a region are identical up to a scale factor, regional Bayesian models allow parameters to vary and express that variation as probabilistic uncertainty.

**Important note**: The target site's own data must be **excluded** when estimating the regional prior hyper-parameters — otherwise the prior would be informed by the data it is supposed to be independent of, compromising Bayesian integrity.

Research has shown that regional Bayesian models outperform local MLE and traditional Index Flood models particularly for records shorter than 15 years.

### The Australian LFRM

The **Large Flood Regionalisation Model (LFRM)** is designed for estimating rare floods in ungauged or data-poor Australian catchments. It pools maximum observed floods from many sites after standardising for at-site variations in mean and coefficient of variation.

A critical feature of the LFRM is its treatment of **inter-site dependence**: large storm events often affect multiple gauge stations simultaneously, meaning the stations are not statistically independent. Ignoring this correlation artificially inflates the effective sample size and leads to systematic underestimation of flood risk.

The LFRM addresses this using an effective number of independent stations $N_e$:

$$\frac{\ln N_e}{\ln N} = a + b\bar{\rho}$$

where $N$ is the total number of sites and $\bar{\rho}$ is the average inter-site correlation. Accounting for $N_e$ prevents underestimation of the 1-in-1000 year flood — the typical design standard for major Australian infrastructure.

---

## Joint Probability Frameworks

For complex systems where flood risk depends on the interaction of multiple variables — not just rainfall depth — a **joint probability framework** is more appropriate than any single-site FFA.

### Example: a coastal river with a dam

Flood risk at a downstream location may depend on:
- Rainfall amount and temporal pattern
- Spatial pattern of rainfall (upstream vs downstream of the dam)
- Initial reservoir level (drawdown)
- Tidal level at the river mouth

Rather than assuming a single "worst-case" combination, the joint probability framework uses **Monte Carlo simulation** to sample thousands of realistic scenarios from the joint distribution of these variables.

Because full hydrodynamic models are too slow to run for each scenario, a **multi-dimensional look-up table** is constructed from a limited number of model runs (e.g., 60 runs covering a range of tidal levels and inflows). This table is then embedded in a faster hydrologic model to evaluate all simulated scenarios.

This is the standard approach for flood risk assessment at complex infrastructure in Queensland and is referenced in ARR 2019 Chapter 7 (Joint Probability).

---

## Non-Stationarity

All methods described here assume **stationarity** — that the flood distribution does not change over time. This assumption is increasingly questionable for catchments affected by:

- **Urbanisation**: Increasing impervious area alters the location and scale parameters over time ($\mu(t)$, $\sigma(t)$).
- **Climate change**: Shifting rainfall intensity distributions alter the frequency of extreme events.

Non-stationary GEV models allow parameters to be functions of time or covariates, e.g.:

$$\ln \sigma(t) = \phi_0 + \phi_1 t$$

This is an active research area. `pyFloodExtremes` currently implements stationary models only — non-stationarity is flagged as a future extension.
