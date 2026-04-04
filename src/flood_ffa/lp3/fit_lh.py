"""
LP3 Parameter Estimation via LH-moments.
"""

import numpy as np
from scipy import optimize
from typing import Tuple, Optional
from flood_ffa.stats.lh_moments import (
    calculate_sample_pwms, 
    pwms_to_lh_moments, 
    get_p3_theoretical_pwms
)

def fit_lp3_lh(data: np.ndarray, shift: int = 0) -> dict:
    """
    Estimate LP3 parameters (mu, sigma, skew) using LH-moments of log-flows.
    """
    log_data = np.log(data)
    
    # 1. Calculate sample PWMs and LH-moments of log-flows
    sample_pwms = calculate_sample_pwms(log_data, max_k=shift + 4)
    sample_lh = pwms_to_lh_moments(sample_pwms, shift=shift)
    
    def objective(params):
        mu, sigma, skew = params
        if sigma <= 0:
            return [1e9, 1e9, 1e9]
        
        # P3 PWMs are more numerically sensitive, restrict skew range
        if abs(skew) > 8.0:
            return [1e9, 1e9, 1e9]
            
        theo_pwms = get_p3_theoretical_pwms(mu, sigma, skew, max_k=shift + 2)
        return [
            theo_pwms[shift] - sample_pwms[shift],
            theo_pwms[shift+1] - sample_pwms[shift+1],
            theo_pwms[shift+2] - sample_pwms[shift+2]
        ]

    # Initial guess using product moments of log-data
    initial_guess = [np.mean(log_data), np.std(log_data), 0.0]
    
    # Use least_squares for robustness over root.
    # max_nfev is raised from the default (100*n=300) because get_p3_theoretical_pwms
    # uses numerical integration, making the objective expensive and gradient
    # estimates noisy. Also accept near-converged solutions (cost < 1e-6) even
    # when success=False (status=0, max evaluations hit).
    sol = optimize.least_squares(
        objective,
        initial_guess,
        bounds=([-np.inf, 1e-6, -8], [np.inf, np.inf, 8]),
        ftol=1e-4,
        max_nfev=3000,
    )

    converged = sol.success or (sol.cost < 1e-6)
    if converged:
        mu, sigma, skew = sol.x
        
        theo_pwms_all = get_p3_theoretical_pwms(mu, sigma, skew, max_k=shift + 3)
        theo_lh = pwms_to_lh_moments(theo_pwms_all, shift=shift)
        
        return {
            "mu": mu,
            "sigma": sigma,
            "skew": skew,
            "shift": shift,
            "success": True,
            "lh_moments": sample_lh,
            "theo_lh_moments": theo_lh
        }
    else:
        return {"success": False, "message": sol.message, "cost": sol.cost}

from scipy.stats import pearson3

def get_lp3_quantile(mu: float, sigma: float, skew: float, aep_pct: float) -> float:
    """
    Calculate LP3 quantile for a given AEP (percent).
    """
    p = 1 - aep_pct / 100.0
    log_q = pearson3.ppf(p, skew, loc=mu, scale=sigma)
    return np.exp(log_q)
