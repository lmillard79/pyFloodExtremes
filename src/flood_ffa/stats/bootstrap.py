"""
Parametric Bootstrap for Uncertainty Estimation in LH-moments fitting.
"""

import numpy as np
import pandas as pd
from typing import Callable, List, Dict
from scipy.stats import genextreme, pearson3

def run_parametric_bootstrap(
    fit_func: Callable,
    quantile_func: Callable,
    params: dict,
    n_obs: int,
    aep_grid: np.ndarray,
    n_sim: int = 1000,
    dist_type: str = "gev"
) -> np.ndarray:
    """
    Perform parametric bootstrap to estimate quantile uncertainty.
    
    Parameters
    ----------
    fit_func : function
        Function to fit the distribution (e.g. fit_gev_lh).
    quantile_func : function
        Function to calculate quantiles (e.g. get_gev_quantile).
    params : dict
        Parameters of the original fit.
    n_obs : int
        Number of observations in original data.
    aep_grid : np.ndarray
        AEP values (percent) to estimate quantiles for.
    n_sim : int
        Number of bootstrap simulations.
    dist_type : str
        'gev' or 'lp3'.
        
    Returns
    -------
    np.ndarray
        Array of shape (n_sim, len(aep_grid)) containing simulated quantiles.
    """
    shift = params["shift"]
    bootstrap_quantiles = np.zeros((n_sim, len(aep_grid)))
    
    # 1. Setup sampling distribution
    if dist_type == "gev":
        # Scipy genextreme uses c = -xi
        rv = genextreme(c=-params["xi"], loc=params["mu"], scale=params["sigma"])
    elif dist_type == "lp3":
        # Sample log-flows then exponentiate if needed, or sample directly?
        # Better to sample log-flows from Pearson3
        rv_log = pearson3(params["skew"], loc=params["mu"], scale=params["sigma"])
    else:
        raise ValueError(f"Unsupported distribution type: {dist_type}")
        
    for i in range(n_sim):
        # 2. Generate synthetic sample
        if dist_type == "gev":
            sim_data = rv.rvs(size=n_obs)
        else:
            sim_data = np.exp(rv_log.rvs(size=n_obs))
            
        # 3. Re-fit using same shift
        sim_fit = fit_func(sim_data, shift=shift)
        
        if sim_fit["success"]:
            # 4. Calculate quantiles
            if dist_type == "gev":
                bootstrap_quantiles[i, :] = [
                    quantile_func(sim_fit["mu"], sim_fit["sigma"], sim_fit["xi"], aep)
                    for aep in aep_grid
                ]
            else:
                bootstrap_quantiles[i, :] = [
                    quantile_func(sim_fit["mu"], sim_fit["sigma"], sim_fit["skew"], aep)
                    for aep in aep_grid
                ]
        else:
            # If fit fails, use NaN
            bootstrap_quantiles[i, :] = np.nan
            
    return bootstrap_quantiles
