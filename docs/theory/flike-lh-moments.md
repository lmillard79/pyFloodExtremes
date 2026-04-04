# FLIKE and the LH-moments Method

## What is FLIKE?

**FLIKE** (now TUFLOW FLIKE, originally developed by Kuczera 1999) is the standard software for at-site flood frequency analysis in Australian practice. It fits probability distributions to an Annual Maximum Series using two complementary approaches:

1. A **Bayesian inference framework** — produces full posterior distributions over parameters.
2. An **LH-moments framework** — a fast, robust frequentist method described in detail below.

`pyFloodExtremes` emulates the LH-moments workflow in Notebook 6 (`06_flike_emulator.ipynb`).

---

## Probability Weighted Moments (PWMs)

Both L-moments and LH-moments are built on **Probability Weighted Moments (PWMs)**. The $k$-th PWM of a sample of $n$ ranked observations $x_{(1)} \leq x_{(2)} \leq \cdots \leq x_{(n)}$ is:

$$b_k = \frac{1}{n} \sum_{j=k+1}^{n} \frac{\binom{j-1}{k}}{\binom{n-1}{k}} x_{(j)}$$

PWMs are essentially weighted averages of the ranked data, with the weights depending on rank position. They are the building blocks from which L-moments and LH-moments are derived.

---

## L-moments (Hosking 1990)

L-moments are linear combinations of PWMs designed to be analogs of conventional moments (mean, variance, skewness, kurtosis) but with far greater robustness to outliers:

| L-moment | Formula | Conventional analog |
|---|---|---|
| $\lambda_1$ (location) | $b_0$ | Mean |
| $\lambda_2$ (scale) | $2b_1 - b_0$ | Related to standard deviation |
| L-skewness ratio $\tau_3$ | $\lambda_3 / \lambda_2$ | Skewness coefficient |
| L-kurtosis ratio $\tau_4$ | $\lambda_4 / \lambda_2$ | Kurtosis coefficient |

Because L-moments are **linear in the data values** (via rank-based weights), a single extreme observation cannot dominate them the way it can dominate the sample skewness coefficient. This makes L-moment parameter estimates far more stable for short flood records.

**Parameter estimation** works by solving the system of equations that sets the theoretical L-moments of the chosen distribution equal to the sample L-moments — analogous to method of moments but using $\lambda_1, \lambda_2, \tau_3$ instead of mean, variance, skewness.

---

## LH-moments (Wang 1997)

Standard L-moments ($\eta = 0$) weight all observations according to their rank, giving equal aggregate attention to low and high flows. For flood frequency analysis this can be a problem: in many Australian records, drought years produce very small annual maxima that pull the fitted curve downward — even though engineers care almost exclusively about the upper tail.

LH-moments introduce a **shift parameter** $\eta \in \{0, 1, 2, 3, 4\}$ that modifies the weighting to **emphasise higher-ranked observations**:

$$\lambda_r^\eta = \frac{(r+\eta-1)!}{(\eta)!(r-1)!} \sum_{k=0}^{r-1} \frac{(-1)^k \binom{r-1}{k}}{\binom{r+\eta+k-1}{r-1}} b_{\eta+k}$$

The practical effect:

| Shift $\eta$ | Effective behaviour |
|---|---|
| 0 | Standard L-moments — all observations equally weighted |
| 1 | Emphasis on the upper half of the distribution |
| 2 | Focus on roughly the upper third |
| 3–4 | Near-exclusive focus on the upper tail; low flows contribute negligibly |

A higher shift allows the fitted curve to track the behaviour of large floods without being distorted by near-zero drought-year flows.

---

## The FLIKE Workflow

### Step 1: MGBT preprocessing

The Multiple Grubbs-Beck Test detects Potentially Influential Low Flows (PILFs). In the LH-moments context, PILFs are either excluded or treated as censored before fitting.

### Step 2: LH-moment fitting

For a chosen shift $\eta$, the distribution parameters are estimated by solving:

$$\lambda_r^\eta(\text{theoretical}) = \lambda_r^\eta(\text{sample}), \quad r = 1, 2, 3$$

This gives three equations in three unknowns ($\mu, \sigma, \xi$ for GEV; $\mu, \sigma, \gamma$ for LP3). In `pyFloodExtremes`, `scipy.optimize.least_squares` solves this system.

### Step 3: Goodness-of-fit (Z4 test)

The fourth LH-moment $\lambda_4^\eta$ is not used for fitting — it is reserved as a **goodness-of-fit check**. The Z4 test statistic measures how closely the theoretical fourth LH-moment matches the sample:

$$Z_4 = \frac{\lambda_4^\eta(\text{sample}) - \lambda_4^\eta(\text{theoretical})}{\text{SE}(\lambda_4^\eta)}$$

A small $|Z_4|$ confirms the distribution fits the data well at the chosen shift.

### Step 4: Optimised shift selection

FLIKE tests $\eta = 0$ through 4 and selects the **smallest shift that passes the Z4 test**. The optimised shift balances two goals:
- Use the lowest shift possible (to retain information from the full record).
- Increase the shift only as far as needed to achieve an adequate fit in the upper tail.

For the example dataset, $\eta = 0$ (standard L-moments) is typically selected — because the record has no problematic low flows (confirmed by MGBT), so no additional up-weighting is needed.

### Step 5: Parametric bootstrap

Uncertainty bounds are estimated by:
1. Simulating $N$ synthetic datasets of the same length from the fitted distribution.
2. Refitting the model to each synthetic dataset using the same shift.
3. Computing the 5th and 95th percentile of the resulting quantile estimates.

This gives a **90% bootstrap confidence interval** — the interval within which 90% of refitted estimates from datasets of this length would fall.

---

## LH-moments vs Bayesian: when to use each

| Consideration | LH-moments (FLIKE) | Bayesian (pyFloodExtremes) |
|---|---|---|
| Speed | Seconds | Minutes (MCMC) |
| Regulatory use | ARR standard (TUFLOW FLIKE) | Not yet standard but growing |
| Prior information | Not incorporated | Formally included via priors |
| Short records | Less reliable | Regularised by prior |
| Censored data | Limited | Incorporated in likelihood |
| Uncertainty expression | 90% bootstrap CI | 94% HDI (full posterior) |
| Output comparability | Matches FLIKE software | Comparable to FLIKE Bayesian mode |

For most Australian regulatory applications, running both and comparing the results is good practice — consistent estimates from both approaches increase confidence; large discrepancies warrant investigation.

---

## References

- Hosking, J.R.M. (1990). L-moments: analysis and estimation of distributions using linear combinations of order statistics. *Journal of the Royal Statistical Society B*, 52(1), 105–124.
- Wang, Q.J. (1997). LH moments for statistical analysis of extreme events. *Water Resources Research*, 33(12), 2841–2848.
- Kuczera, G. (1999). *FLIKE: A computer program for Bayesian and classical flood frequency analysis*. University of Newcastle.
- Ball, J. et al. (2019). *Australian Rainfall and Runoff*. Geoscience Australia.
