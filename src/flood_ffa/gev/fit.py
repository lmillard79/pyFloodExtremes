import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

def gev_logp(value, mu, sigma, xi):
    """
    Log-probability function for the Generalised Extreme Value (GEV) distribution,
    implemented using PyMC's math (PyTensor) functions for NUTS compatibility.
    """
    z = (value - mu) / sigma
    cond = 1 + xi * z
    
    # To prevent log(negative) breaking gradients during exploration, we substitute
    # an arbitrary positive value where cond <= 0, and later switch those to -inf.
    safe_cond = pm.math.switch(cond > 0, cond, 1e-10)
    
    log_t = - (1 / xi) * pm.math.log(safe_cond)
    t = pm.math.exp(log_t)
    
    logp_val = -pm.math.log(sigma) + (xi + 1) * log_t - t
    
    # Apply -inf probability where 1 + xi * z <= 0
    logp_val = pm.math.switch(cond > 0, logp_val, -np.inf)
    
    return pm.math.sum(logp_val)

def fit_gev(flows: pd.Series, draws: int = 2000, tune: int = 1000) -> az.InferenceData:
    """
    Fits a single-population GEV distribution to an annual maximum series (AMS)
    using PyMC MCMC sampling.
    
    Priors are weakly informative, suitable for Australian flood practice:
    - xi prior is centred on 0 (Gumbel), as Australian streams often have shape near 0.
    """
    with pm.Model() as model:
        mu = pm.Normal("mu", mu=flows.mean(), sigma=flows.std())
        sigma = pm.HalfNormal("sigma", sigma=flows.std())
        xi = pm.Normal("xi", mu=0.0, sigma=0.2)
        
        obs = pm.CustomDist(
            "obs",
            mu,
            sigma,
            xi,
            logp=gev_logp,
            observed=flows.values,
        )
        
        idata = pm.sample(draws=draws, tune=tune, return_inferencedata=True)
        
    return idata
