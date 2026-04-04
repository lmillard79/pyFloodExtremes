# Statistical Inference Methods for Flood Frequency Analysis

Four principal methods exist for estimating the parameters of a flood frequency distribution from data. `pyFloodExtremes` implements two of them (Bayesian MCMC and LH-moments) and this document explains all four so you understand where each fits.

---

## 1. Method of Moments (MoM) and Expected Moments Algorithm (EMA)

The traditional approach estimates parameters by matching the sample **mean**, **variance**, and **skewness** to their theoretical equivalents for the chosen distribution.

**Weakness**: Sample moments — especially skewness — are highly sensitive to outliers. A single extraordinary flood year can dominate the skewness estimate and destabilise the entire fit. For short records (under 30 years), MoM estimates are unreliable.

The **Expected Moments Algorithm (EMA)** is a modern generalisation of MoM used in the US Bulletin 17C guidelines. It extends the framework to incorporate:
- Historical floods that occurred before the gauge was installed
- **Censored data** — years where all we know is that the flow was below a threshold (e.g., MGBT-detected low outliers)
- Regional skewness information

EMA is directly related to the FLIKE workflow for LP3 fitting with PILFs.

---

## 2. Maximum Likelihood Estimation (MLE)

MLE finds the parameter values that maximise the probability of observing the recorded data — the "most likely" explanation.

**Strengths**: Theoretically well-motivated, asymptotically efficient for large samples.

**Weaknesses for flood frequency analysis**:
- Provides only a **single point estimate** rather than a distribution of uncertainty.
- To describe uncertainty, MLE relies on asymptotic normality assumptions (Fisher Information Matrix). These assumptions can **severely underestimate** the true uncertainty of flood quantiles, particularly for skewed distributions like LP3 and for short records.
- When the dataset contains complex measurement errors or outliers, the likelihood function can have multiple local optima, making single-mode MLE unreliable.

---

## 3. L-moments and LH-moments

**L-moments** (Hosking 1990) replace conventional sample moments with **linear combinations of order statistics** (ranked data). They are far less sensitive to outliers than product-moments, making them robust for flood records where extreme events would otherwise dominate the skewness estimate.

**LH-moments** (Wang 1997) extend L-moments with a shift parameter $\eta \in \{0,1,2,3,4\}$ that progressively up-weights higher-ranked (larger) observations, focusing the fit on the upper tail. This is particularly useful when the record contains influential low flows.

This is the method used by **TUFLOW FLIKE** — the standard Australian frequentist FFA tool. See [`flike-lh-moments.md`](flike-lh-moments.md) for details.

**Limitation**: L-moments cannot easily incorporate regional prior information, historical data, or censored observations without special adjustments. For short or data-poor records, Bayesian methods are more appropriate.

---

## 4. Bayesian Inference

Bayesian inference is the most flexible framework for flood frequency analysis, and the primary method in `pyFloodExtremes`.

### The framework

Instead of finding a single "best" parameter estimate, the Bayesian approach treats the parameters as **random variables** and produces a full **posterior distribution** over all plausible parameter values, given the data.

The posterior is computed using **Bayes' Theorem**:

$$P(\theta \mid \text{data}) \propto P(\text{data} \mid \theta) \times P(\theta)$$

where:
- $P(\theta \mid \text{data})$ — the **posterior**: what we believe about the parameters *after* seeing the data
- $P(\text{data} \mid \theta)$ — the **likelihood**: how probable is the observed data for a given set of parameters
- $P(\theta)$ — the **prior**: what we believed about the parameters *before* seeing the data

### Priors in pyFloodExtremes

The prior encodes engineering judgement before the data are considered. For example:
- The GEV shape parameter $\xi \sim \text{Normal}(0, 0.2)$ — centred at Gumbel (zero), with a tight spread reflecting that Australian streams rarely have extreme shape parameters.
- The LP3 skewness $\gamma \sim \text{Normal}(0, 0.5)$ — centred at zero, reflecting ARR guidance that many Australian catchments are near-symmetric in log-space.

These are **weakly informative priors** — they provide regularisation for short records while allowing the data to override them when there is sufficient evidence.

### MCMC sampling

Evaluating the posterior analytically is generally impossible. `pyFloodExtremes` uses PyMC's **NUTS** (No U-Turn Sampler) — a state-of-the-art Hamiltonian Monte Carlo algorithm — to draw thousands of samples from the posterior. These samples are then used to compute return level uncertainty bands directly.

### Key advantages over MLE

| Feature | MLE | Bayesian |
|---|---|---|
| Uncertainty representation | Asymptotic approximation (often underestimates) | Full posterior — naturally asymmetric and accurate |
| Prior information | Not incorporated | Formally included |
| Short records | Unreliable | Regularised by prior |
| Censored / historical data | Difficult | Incorporated in likelihood |
| Output | Point estimate + approximate CI | Full distribution → HDI |

### Expected parameter vs expected probability quantiles

The Bayesian framework produces two conceptually different types of design quantile:

- **Expected parameter quantile**: The return level at the *posterior mean* parameter values. Minimises bias in estimating flood *magnitude*.
- **Expected probability quantile**: The return level averaged over the full posterior distribution. Minimises bias in the *exceedance probability* of a flood — important for risk analysis where you need accurate probability statements rather than accurate magnitude statements.

`pyFloodExtremes` reports the **posterior median** return level (robust to the skewed posteriors that arise for rare events) and the **94% Highest Density Interval (HDI)**.

---

## Comparison summary

| Method | Uncertainty | Regional info | Censored data | Computational cost | Used in |
|---|---|---|---|---|---|
| MoM / EMA | Approximate | Via regional skew | Yes (EMA) | Low | Bulletin 17B/C |
| MLE | Asymptotic | No | Possible | Low | General statistics |
| L/LH-moments | Bootstrap | Limited | Restricted | Low | FLIKE, ARR |
| Bayesian MCMC | Full posterior | Via prior | Yes | Medium–high | pyFloodExtremes, FLIKE Bayesian |
