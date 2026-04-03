import numpy as np
import pandas as pd
import pymc as pm
import arviz as az

def lp3_logp(value, mu, sigma, skew):
    """
    Log-probability function for the Pearson Type 3 distribution,
    implemented using PyTensor math to allow NUTS sampling gradients.
    """
    z = (value - mu) / sigma
    
    # Prevent division by zero if skew is exactly 0
    safe_skew = pm.math.switch(pm.math.eq(skew, 0), 1e-8, skew)
    
    alpha = 4.0 / (safe_skew ** 2)
    beta = 2.0 / safe_skew
    
    u = beta * z + alpha
    
    # The condition for the support of the distribution is u > 0.
    # To prevent log(negative) breaking gradients during exploration, we substitute
    # an arbitrary positive value where u <= 0, and switch to -inf at the end.
    safe_u = pm.math.switch(u > 0, u, 1e-10)
    
    log_f_u = (alpha - 1) * pm.math.log(safe_u) - safe_u - pm.math.gammaln(alpha)
    
    # Jacobian for the transformation from u to value
    jacobian = pm.math.log(pm.math.abs(beta) / sigma)
    
    logp_val = log_f_u + jacobian
    
    # Apply -inf probability where u <= 0 (outside the support)
    logp_val = pm.math.switch(u > 0, logp_val, -np.inf)
    
    # Fallback to normal distribution if skew is strictly 0 (limit as skew -> 0)
    normal_logp = -pm.math.log(sigma * np.sqrt(2 * np.pi)) - 0.5 * (z ** 2)
    logp_val = pm.math.switch(pm.math.eq(skew, 0), normal_logp, logp_val)
    
    return pm.math.sum(logp_val)

def fit_lp3(flows: pd.Series, draws: int = 2000, tune: int = 1000) -> az.InferenceData:
    """
    Fits a Log-Pearson Type 3 (LP3) distribution to an annual maximum series (AMS).
    This is the default distribution in Australian Rainfall and Runoff (ARR).
    
    All fitting is performed in log-space.
    """
    log_flows = np.log(flows.values)
    
    with pm.Model() as model:
        mu = pm.Normal("mu", mu=log_flows.mean(), sigma=log_flows.std())
        sigma = pm.HalfNormal("sigma", sigma=log_flows.std())
        skew = pm.Normal("skew", mu=0.0, sigma=0.5)  # ARR suggests near-zero for many catchments
        
        obs = pm.CustomDist(
            "obs",
            mu,
            sigma,
            skew,
            logp=lp3_logp,
            observed=log_flows,
        )
        
        idata = pm.sample(draws=draws, tune=tune, return_inferencedata=True)
        
    return idata
