# Extreme Value Theory and the GEV Distribution

## What is Flood Frequency Analysis?

Flood Frequency Analysis (FFA) answers a practical engineering question: *how large is the flood that occurs, on average, once every T years?* The answer drives the design of dams, levees, culverts, bridges, and flood-plain zoning.

Rather than predicting *when* floods occur, FFA estimates their **magnitude** at a given **Annual Exceedance Probability (AEP)** — the probability that a given flow level will be exceeded in any one year. AEP and Average Recurrence Interval (ARI) are related by:

$$\text{AEP\%} = \frac{100}{T}$$

So a 1% AEP flood is the same as the 100-year ARI flood.

## The Annual Maximum Series

The input to FFA is an **Annual Maximum Series (AMS)**: the single largest recorded flow in each year. By taking one value per year, the AMS removes seasonal structure and produces a series that can be modelled as independent observations from an extreme value distribution.

## Why the GEV Distribution?

The theoretical foundation for AMS analysis is the **Fisher–Tippett–Gnedenko theorem**: regardless of the underlying distribution of individual flood events, the distribution of annual maxima converges to one of three limiting forms as record length increases. These three forms are unified by the **Generalised Extreme Value (GEV) distribution**:

$$G(z) = \exp\left\{-\left[1 + \xi\left(\frac{z - \mu}{\sigma}\right)\right]^{-1/\xi}\right\}$$

### The three parameters

| Parameter | Symbol | Meaning |
|---|---|---|
| Location | $\mu$ | Shifts the distribution — approximately the median annual maximum |
| Scale | $\sigma > 0$ | Controls the spread — analogous to the standard deviation |
| Shape | $\xi$ | Determines tail behaviour — the most critical parameter for rare events |

### The shape parameter $\xi$ and tail behaviour

| $\xi$ | Distribution type | Upper tail | Practical implication |
|---|---|---|---|
| $\xi > 0$ | Fréchet | Heavy, unbounded | No finite upper bound on flood magnitude; rare events can be very large |
| $\xi = 0$ | Gumbel | Light (exponential decay) | Classic engineering assumption; bounded growth with return period |
| $\xi < 0$ | Weibull | Bounded above | A finite maximum possible flood exists |

For Australian flood records, $\xi$ is typically small and positive — a moderately heavy tail. The presence of an extraordinary event in the record (like the 2021 flood in the example dataset) can substantially increase the estimated $\xi$, which then inflates design flood estimates at all return periods.

## Return Level Calculation

Given GEV parameters $(\mu, \sigma, \xi)$, the return level at AEP $p$% (i.e., the flow exceeded with probability $p/100$ in any year) is:

$$Q_T = \mu + \frac{\sigma}{\xi}\left[\left(-\ln\left(1 - \frac{p}{100}\right)\right)^{-\xi} - 1\right] \quad (\xi \neq 0)$$

For the Gumbel limit ($\xi = 0$):

$$Q_T = \mu - \sigma \ln\left(-\ln\left(1 - \frac{p}{100}\right)\right)$$

## Generalised Pareto Distribution (GPD)

An alternative to the AMS approach is **Peaks Over Threshold (POT)** analysis, which models all flood events exceeding a chosen threshold — not just the annual maximum. The GPD is theoretically justified for exceedances:

$$F(x) = 1 - \left(1 + \frac{\xi(x - \mu)}{\sigma}\right)^{-1/\xi}$$

POT analysis uses more of the available data (multiple events per year) but requires careful threshold selection and modelling of event occurrence rates. `pyFloodExtremes` currently implements AMS / GEV analysis only.

## Further Reading

- Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values*. Springer.
- Ball, J. et al. (2019). *Australian Rainfall and Runoff: A Guide to Flood Estimation*. Geoscience Australia.
