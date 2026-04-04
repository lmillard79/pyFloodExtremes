Within the context of flood frequency analysis (FFA), the provided sources discuss "key parameters" primarily as the fundamental statistical variables that define probability distributions (such as location, scale, and shape). The sources explore how these parameters are estimated, refined, and interpreted across different statistical and modeling frameworks, including traditional moment-based methods, maximum likelihood estimation, regional regression models, and Bayesian inference.  
Here is a breakdown of how key parameters are treated within these larger statistical frameworks:

### 1\. Defining Key Parameters in Probability Models

In FFA, a mathematical probability distribution is selected to describe flood risk. The shape and bounds of these distributions are controlled by specific key parameters:

* **Generalized Extreme Value (GEV) and Generalized Pareto (GP) Distributions:** These distributions rely on a **location** parameter ($\\mu$), a **scale** parameter ($\\sigma$), and a **shape** parameter ($\\xi$) 1-4. The shape parameter (or tail-index) heavily influences the behavior of the distribution's tail, dictating the frequency of extreme events 5, 6\.  
* **Log-Pearson Type III (LP3) Distribution:** Recommended by guidelines such as Bulletin 17C, the LP3 distribution is defined by **location** ($\\tau$), **shape** ($\\alpha$), and **scale** ($\\beta$) parameters 7\. In practice, these parameters are estimated using the sample moments of the log-transformed annual maximum flood series: the **mean**, **standard deviation**, and **skewness** 8-10. The uncertainty of the skew parameter, in particular, has a profound, non-linear impact on estimating flood quantiles and expected flood damages 11-13.

### 2\. Parameter Estimation Frameworks (EMA, MLE, and L-Moments)

Different statistical frameworks dictate how these key parameters are calculated from available flood data:

* **Method of Moments & Expected Moments Algorithm (EMA):** Traditional moments estimate parameters directly from the mean, variance, and skew of the sample data 14\. The Expected Moments Algorithm (EMA) is a generalization of this framework that allows for the incorporation of historical floods, interval data, and censored data (like potentially influential low floods, or PILFs) alongside systematic streamgage records 15-17.  
* **Maximum Likelihood Estimation (MLE):** MLE frameworks maximize a likelihood function to find parameter estimates (e.g., $\\hat{\\xi}*{ML}$ and $\\hat{\\beta}*{ML}$) 18\. While MLE provides estimators with good statistical properties, it relies on asymptotic assumptions to determine parameter uncertainty, which can result in confidence intervals that do not accurately represent the true, skewed nature of parameter uncertainty 19-22. Furthermore, when measurement errors are introduced, MLE can struggle with multiple optima 23-25.  
* **L-Moments:** Utilizing linear combinations of order statistics, the L-moments framework is widely used to estimate parameters for distributions like the GEV because the resulting parameters are less sensitive to extreme outliers than those derived from traditional product-moments 14, 26, 27\.

### 3\. The Bayesian Framework

The sources strongly emphasize the **Bayesian framework** as a superior method for handling parameter uncertainty. In classical statistics, parameters are often treated as fixed but unknown values; in the Bayesian framework, the true value of a parameter is summarized by a probability distribution (the posterior distribution) that reflects what is known given the data and prior information 28-32.

* **MCMC Simulation:** Tools like RMC-BestFit and FLIKE use Markov Chain Monte Carlo (MCMC) simulations or importance sampling to sample thousands of plausible parameter sets (e.g., generating joint distributions of standard deviation and skewness) to build an empirical approximation of the parameter's posterior distribution 33-38.  
* **Expected Parameter vs. Expected Probability:** The Bayesian framework allows software to output two distinct types of design quantiles. **Expected parameter quantiles** are based on a single set of mean or most likely parameter values and are used to minimize bias in estimating the *magnitude* of a design flood. **Expected probability quantiles** are derived by integrating over the full distribution of plausible parameters and are used to minimize bias in the *exceedance probability* of a flood, which is crucial for risk analyses 39-44.

### 4\. Regional Flood Frequency Estimation (RFFE) Frameworks

When at-site data is too short or unreliable, frameworks expand to incorporate regional data, treating parameters spatially:

* **Parameter Regression Technique (PRT) and GLS:** Under Regional Flood Frequency Estimation (RFFE), the Parameter Regression Technique regresses the parameters of a distribution (such as the mean, standard deviation, and skew of the LP3 distribution) against catchment characteristics (like area or design rainfall) 45-48. This is typically done using **Generalised Least Squares (GLS)** regression, which isolates the underlying model error from the time-sampling error of the parameters 49-51.  
* **Regional Bayesian Models & Hyper-parameters:** In regional Bayesian models (which differ from the traditional Index Flood model), the goal is to define a "prior distribution" for the target site's parameters based on the region. This prior distribution is defined by **hyper-parameters**, which are estimated from a set of "pseudo target site parameters" calculated from other sites in the homogeneous region 52-57.

### 5\. Parameters in Deterministic Rainfall-Runoff Frameworks (Causal Information)

Beyond purely statistical distributions, FFA also utilizes deterministic rainfall-runoff models (like RORB or SWMM) to simulate flood volumes. In this context, the key parameters are physical or inferred system behaviors rather than statistical moments:

* **Routing and Loss Parameters:** These include initial rainfall loss, continuing loss, and routing parameters (like $k\_c$ and the non-linearity parameter $m$) 58-61.  
* **Stochastic Uncertainty:** Because these parameters are highly uncertain, modern frameworks treat them stochastically in a Monte Carlo joint probability framework. By randomly generating thousands of parameter realisations (e.g., varying the $k\_c$ parameter according to a Beta distribution), modelers can construct a volumetric flood frequency curve and extract realistic confidence limits for the resulting flood quantiles 61-63.

