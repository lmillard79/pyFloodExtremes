"""
GEV Parameter Estimation via LH-moments.
"""

import numpy as np
from scipy import optimize
from typing import Tuple, Optional
from flood_ffa.stats.lh_moments import (
    calculate_sample_pwms, 
    pwms_to_lh_moments, 
    get_gev_theoretical_pwms
)

def fit_gev_lh(data: np.ndarray, shift: int = 0) -> dict:
    """
    Estimate GEV parameters (mu, sigma, xi) using LH-moments of order 'shift'.
    """
    # 1. Calculate sample PWMs and LH-moments
    sample_pwms = calculate_sample_pwms(data, max_k=shift + 4)
    sample_lh = pwms_to_lh_moments(sample_pwms, shift=shift)
    
    # We want to match theoretical PWMs: beta_h, beta_{h+1}, beta_{h+2}
    # to sample PWMs: b_h, b_{h+1}, b_{h+2}
    
    def objective(params):
        mu, sigma, xi = params
        if sigma <= 0 or xi >= 1.0 or xi <= -1.0: # Numerical stability
            return [1e9, 1e9, 1e9]
        
        theo_pwms = get_gev_theoretical_pwms(mu, sigma, xi, max_k=shift + 2)
        # Match b_h, b_{h+1}, b_{h+2}
        return [
            theo_pwms[shift] - sample_pwms[shift],
            theo_pwms[shift+1] - sample_pwms[shift+1],
            theo_pwms[shift+2] - sample_pwms[shift+2]
        ]

    # Initial guess using standard L-moments (h=0) if shift=0, or sample stats
    std = np.std(data)
    mean = np.mean(data)
    initial_guess = [mean, std * 0.6, 0.1]
    
    # Use least_squares for robustness over root
    sol = optimize.least_squares(
        objective, 
        initial_guess, 
        bounds=([-np.inf, 1e-6, -0.99], [np.inf, np.inf, 0.99]),
        ftol=1e-4
    )
    
    if sol.success:
        mu, sigma, xi = sol.x
        
        # Calculate Goodness of Fit (Z4 test)
        # Z4 = (lambda_4_sample - lambda_4_theo) / SE(lambda_4)
        # For simplicity in this emulator, we'll return the error in lambda_4
        theo_pwms_all = get_gev_theoretical_pwms(mu, sigma, xi, max_k=shift + 3)
        theo_lh = pwms_to_lh_moments(theo_pwms_all, shift=shift)
        
        # error_lh4 = (sample_lh[3] - theo_lh[3]) / sample_lh[1] # Normalised by scale
        
        return {
            "mu": mu,
            "sigma": sigma,
            "xi": xi,
            "shift": shift,
            "success": True,
            "lh_moments": sample_lh,
            "theo_lh_moments": theo_lh
        }
    else:
        return {"success": False, "message": sol.message}

def get_gev_quantile(mu: float, sigma: float, xi: float, aep_pct: float) -> float:
    """
    Calculate GEV quantile for a given AEP (percent).

    For non-exceedance probability F = 1 - AEP/100 and reduced variate y = -ln(F):
        Q = mu + (sigma/xi) * (y^{-xi} - 1)   [xi != 0]
        Q = mu - sigma * ln(y)                  [xi == 0, Gumbel]

    Note: xi > 0 denotes a heavy-tailed (Frechet) distribution.
    """
    F = 1.0 - aep_pct / 100.0          # non-exceedance probability
    y = -np.log(F)                      # reduced variate (always positive for F in (0,1))
    if abs(xi) < 1e-8:
        return mu - sigma * np.log(y)   # Gumbel limit
    else:
        return mu + (sigma / xi) * (y ** (-xi) - 1)
