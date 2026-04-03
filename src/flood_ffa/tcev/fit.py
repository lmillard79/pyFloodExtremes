import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

def tcev_logp(value, w, mu1, sigma1, xi1, mu2, sigma2, xi2):
    """
    Log-probability function for the Two-Component Extreme Value (TCEV) mixture model.
    """
    # Component 1 (Ordinary)
    z1 = (value - mu1) / sigma1
    cond1 = 1 + xi1 * z1
    safe_cond1 = pm.math.switch(cond1 > 0, cond1, 1e-10)
    log_t1 = - (1 / xi1) * pm.math.log(safe_cond1)
    t1 = pm.math.exp(log_t1)
    logp1 = -pm.math.log(sigma1) + (xi1 + 1) * log_t1 - t1
    logp1 = pm.math.switch(cond1 > 0, logp1, -np.inf)
    
    # Component 2 (Extraordinary)
    z2 = (value - mu2) / sigma2
    cond2 = 1 + xi2 * z2
    safe_cond2 = pm.math.switch(cond2 > 0, cond2, 1e-10)
    log_t2 = - (1 / xi2) * pm.math.log(safe_cond2)
    t2 = pm.math.exp(log_t2)
    logp2 = -pm.math.log(sigma2) + (xi2 + 1) * log_t2 - t2
    logp2 = pm.math.switch(cond2 > 0, logp2, -np.inf)
    
    # Mixture weights in log-space
    log_w1 = pm.math.log(1 - w)
    log_w2 = pm.math.log(w)
    
    # Combine using logsumexp strategy for numerical stability
    comp1_term = log_w1 + logp1
    comp2_term = log_w2 + logp2
    
    max_term = pm.math.maximum(comp1_term, comp2_term)
    
    # pm.math.exp is safe here because the argument is <= 0
    logp_mix = max_term + pm.math.log(
        pm.math.exp(comp1_term - max_term) + pm.math.exp(comp2_term - max_term)
    )
    
    return pm.math.sum(logp_mix)

def fit_tcev(flows: pd.Series, draws: int = 2000, tune: int = 1000) -> az.InferenceData:
    """
    Fits a Two-Component Extreme Value (TCEV) mixture model to an AMS.
    Component 1 represents ordinary floods, Component 2 represents extraordinary floods.
    Includes an ordering constraint (mu1 < mu2) to prevent label switching.
    """
    with pm.Model() as model:
        # Mixing weight -- prior favours extraordinary floods being rare
        w = pm.Beta("w", alpha=1, beta=10)

        # Component 1 -- ordinary floods
        mu1 = pm.Normal("mu1", mu=flows.mean(), sigma=flows.std())
        sigma1 = pm.HalfNormal("sigma1", sigma=flows.std())
        xi1 = pm.Normal("xi1", mu=0.0, sigma=0.2)

        # Component 2 -- extraordinary floods
        # Prior centres mu2 above component 1, near the 90th percentile
        mu2 = pm.Normal("mu2", mu=flows.quantile(0.9), sigma=flows.std())
        sigma2 = pm.HalfNormal("sigma2", sigma=flows.std())
        xi2 = pm.Normal("xi2", mu=0.0, sigma=0.2)
        
        # Enforce ordering constraint to avoid label switching during sampling
        # We assign a probability of 0 (-inf in log-space) if mu1 >= mu2
        pm.Potential("order_constraint", pm.math.switch(mu1 < mu2, 0.0, -np.inf))

        obs = pm.CustomDist(
            "obs",
            w,
            mu1,
            sigma1,
            xi1,
            mu2,
            sigma2,
            xi2,
            logp=tcev_logp,
            observed=flows.values,
        )
        
        # Higher target_accept recommended for mixture models
        idata = pm.sample(draws=draws, tune=tune, target_accept=0.9, return_inferencedata=True)
        
    return idata
