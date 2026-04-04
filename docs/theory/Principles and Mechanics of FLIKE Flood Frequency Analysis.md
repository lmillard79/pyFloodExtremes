**FLIKE** (now known as TUFLOW FLIKE) is a widely used software package for performing at-site Flood Frequency Analysis (FFA) 1-3. Originally developed by Kuczera in 1999 4, 5, it is designed to estimate design floods and their exceedance probabilities by fitting probability distributions (such as the Generalized Extreme Value (GEV), Log-Pearson Type III (LP3), Gumbel, and Generalized Pareto distributions) to an annual maximum series of flood data 2, 6-8.  
The software works by utilizing two primary parameter estimation and calibration approaches: a **Bayesian inference framework** and the **L-moments/LH-moments approach** 9\.  
Here is a summary of how FLIKE works and its major components regarding L-moments and LH-moments:

### 1\. The L-Moments Approach

**Theory and Purpose:**Developed by Hosking (1990), L-moments were introduced to overcome the bias and sensitivity to outliers that plague traditional method-of-moments (product-moments) estimation 10\. **L-moments are based on linear combinations of order statistics** (data ranked in ascending order) 11, 12\.

* The first L-moment ($\\lambda\_1$) provides a measure of **location** (mean) 13\.  
* The second L-moment ($\\lambda\_2$) provides a measure of **scale** (variance) 13\.  
* The ratios of the higher L-moments ($\\tau\_3$ and $\\tau\_4$) provide measures of **L-skewness** and **L-kurtosis**, respectively, determining the asymmetry and "peakiness" of the distribution 12, 13\.

**How it works in FLIKE:**In FLIKE, the L-moment method involves matching the theoretical L-moments of a selected probability distribution with the sample L-moments calculated directly from the gauged data 14\. Solving these equations yields the parameter estimates, which are then used to calculate specific flood quantiles (e.g., the 1-in-100-year flood) 14\. FLIKE restricts the L-moment approach strictly to applications involving gauged discharge data where rating curve errors or regional priors do not require special attention 10\.

### 2\. The LH-Moments Approach

**Theory and Purpose:**Introduced by Wang (1997), LH-moments are a generalization of L-moments 15, 16\. In many flood records, a large portion of the data consists of low or zero flows 15\. When standard L-moments are applied, **these frequent, lower discharges can exert undue influence on the statistical fit**, skewing the curve and providing a poor fit for the rarer, high-magnitude discharges that engineers actually care about 15, 16\.  
To fix this, LH-moments introduce a **weighting shift parameter ($\\eta$)**—typically ranging from 0 to 4—which modifies the L-moment equations to place much greater emphasis on the higher-ranked flows (the extreme events) 15, 17\. Standard L-moments are simply a special case of LH-moments where the shift parameter is zero ($\\eta=0$) 18\.  
**How it works in FLIKE:**

* **Optimized Shift Search:** FLIKE allows users to either manually set the shift parameter ($\\eta \= 0, 1, 2, 3,$ or $4$) or use an **Optimized H** function to automatically find the best shift parameter for the data 19, 20\.  
* **Goodness-of-Fit Testing:** FLIKE uses the first three LH-moments to fit the model parameters (such as for the GEV distribution). It then uses the fourth LH-moment to test the adequacy of the fit, generating a test statistic that determines if the distribution is appropriate 19, 21\.  
* **Tailored High-Flow Fitting:** By applying an optimized LH-moment shift, FLIKE can effectively disregard frequent floods (for example, those more frequent than the 50% Annual Exceedance Probability) to provide a highly accurate fit and significantly reduced uncertainty bounds in the upper tail of the flood frequency curve 20, 22\.

### Major Components and Workflow in FLIKE

1. **Data Preparation:** The user imports an annual maximum flood series into the FLIKE editor 8\.  
2. **Censoring / Outlier Detection:** FLIKE includes built-in capabilities, such as the multiple Grubbs-Beck test, to detect and censor Potentially Influential Low Flows (PILFs) so they do not skew the distribution 23, 24\.  
3. **Model Selection:** The user selects a preferred probability model (e.g., LP3 or GEV) and the inference method (Bayesian or LH-moments) 8, 25\.  
4. **Parametric Bootstrap:** To estimate the uncertainty and confidence limits of the LH-moments fit, FLIKE uses a Monte Carlo method known as a parametric bootstrap. It generates many random samples from the fitted distribution, refits the model to these samples, and approximates the sampling distribution to quantify quantile confidence limits 26, 27\.  
5. **Output:** FLIKE outputs a visual probability plot alongside a text-based report file detailing the expected quantiles, confidence limits, and optimal shift parameters 28, 29\.

