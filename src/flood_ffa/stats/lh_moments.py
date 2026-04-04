"""
Linear Higher-order moments (LH-moments) and Probability Weighted Moments (PWMs).
Based on Wang (1997) and Kuczera (1999).
"""

import numpy as np
from scipy.special import comb, gamma, gammaln
from scipy import integrate
from typing import Union, Tuple

def calculate_sample_pwms(data: np.ndarray, max_k: int = 8) -> np.ndarray:
    """
    Calculate unbiased sample Probability Weighted Moments (b_k).
    b_k = (1/n) * sum_{j=k+1}^n [ comb(j-1, k) / comb(n-1, k) ] * x_{(j)}
    where x_{(j)} is the j-th smallest observation.
    """
    n = len(data)
    x = np.sort(data)
    b = np.zeros(max_k + 1)
    
    for k in range(max_k + 1):
        if n <= k:
            continue
        
        # Coefficients for each observation
        # Use log-space for combinations to avoid overflow
        weights = np.zeros(n)
        for j in range(k, n):
            # j is 0-indexed here, so j corresponds to j+1 in the formula
            # weights[j] = comb(j, k) / comb(n-1, k)
            log_w = (gammaln(j + 1) - gammaln(k + 1) - gammaln(j - k + 1)) - \
                    (gammaln(n) - gammaln(k + 1) - gammaln(n - k))
            weights[j] = np.exp(log_w)
            
        b[k] = np.sum(weights * x) / n
        
    return b

def pwms_to_lh_moments(pwms: np.ndarray, shift: int = 0) -> np.ndarray:
    """
    Convert PWMs (b_k) to LH-moments (lambda_r^h) for a given shift h.
    Formulas from Wang (1997).
    """
    h = shift
    if len(pwms) < h + 4:
        raise ValueError(f"Need at least {h+4} PWMs for 4 LH-moments with shift {h}")
    
    lambdas = np.zeros(5) # lambda_1 to lambda_4 (using 1-based indexing for convenience)
    
    # lambda_1^h = (h+1) * b_h
    lambdas[1] = (h + 1) * pwms[h]
    
    # lambda_2^h = (h+1)(h+2)/2 * (2*b_{h+1} - b_h)
    lambdas[2] = (h + 1) * (h + 2) / 2.0 * (2 * pwms[h+1] - pwms[h])
    
    # lambda_3^h = (h+1)(h+2)(h+3)/6 * (6*b_{h+2} - 6*b_{h+1} + b_h)
    lambdas[3] = (h + 1) * (h + 2) * (h + 3) / 6.0 * (6 * pwms[h+2] - 6 * pwms[h+1] + pwms[h])
    
    # lambda_4^h = (h+1)(h+2)(h+3)(h+4)/24 * (20*b_{h+3} - 30*b_{h+2} + 12*b_{h+1} - b_h)
    lambdas[4] = (h + 1) * (h + 2) * (h + 3) * (h + 4) / 24.0 * \
                 (20 * pwms[h+3] - 30 * pwms[h+2] + 12 * pwms[h+1] - pwms[h])
                 
    return lambdas[1:]

def get_gev_theoretical_pwms(mu: float, sigma: float, xi: float, max_k: int = 8) -> np.ndarray:
    """
    Calculate theoretical PWMs for GEV distribution.
    beta_k = (1/(k+1)) * [ mu + (sigma/xi) * (1 - (k+1)^(-xi) * Gamma(1-xi)) ]
    Note: xi follows the standard convention (xi > 0 is heavy-tailed).
    """
    beta = np.zeros(max_k + 1)
    
    # Gamma(1-xi) is defined for xi < 1
    if xi >= 1.0:
        return np.full(max_k + 1, np.nan)
        
    g = gamma(1 - xi)
    
    for k in range(max_k + 1):
        if abs(xi) < 1e-8:
            # Gumbel limit
            # beta_k = (1/(k+1)) * [ mu + sigma * (EulerGamma + log(k+1)) ]
            beta[k] = (1.0 / (k + 1)) * (mu + sigma * (np.euler_gamma + np.log(k + 1)))
        else:
            beta[k] = (1.0 / (k + 1)) * (mu + (sigma / xi) * (1 - (k + 1)**xi * g))
            # Wait, the formula from Hosking (1990) for L-moments uses:
            # beta_k = (1/(k+1)) * [ mu + (sigma/xi) * (1 - (k+1)^xi * Gamma(1-xi)) ] ... no.
            # Let's re-verify GEV PWM formula.
            # x(F) = mu + (sigma/xi) * (1 - (-log F)^xi)
            # beta_k = integral_0^1 x(F) F^k dF
            # beta_k = mu/(k+1) + (sigma/xi) * [ 1/(k+1) - integral_0^1 (-log F)^xi F^k dF ]
            # Substitute u = -log F, F = exp(-u), dF = -exp(-u) du
            # integral = integral_0^inf u^xi exp(-(k+1)u) du
            # Substitute v = (k+1)u, u = v/(k+1), du = dv/(k+1)
            # integral = (k+1)^(-xi-1) * integral_0^inf v^xi exp(-v) dv
            # integral = (k+1)^(-xi-1) * Gamma(1+xi)
            # beta_k = (1/(k+1)) * [ mu + (sigma/xi) * (1 - (k+1)^(-xi) * Gamma(1+xi)) ]
            # This is using xi as shape parameter where xi > 0 is Frechet (heavy tail).
            # PyMC GEV uses xi where xi > 0 is heavy tail.
            # But Scipy genextreme uses c = -xi.
            
    # Corrected formula for standard heavy-tailed xi (xi > 0):
    g_plus = gamma(1 + xi)
    for k in range(max_k + 1):
        if abs(xi) < 1e-8:
            beta[k] = (1.0 / (k + 1)) * (mu + sigma * (np.euler_gamma + np.log(k + 1)))
        else:
            beta[k] = (1.0 / (k + 1)) * (mu + (sigma / xi) * (1 - (k + 1)**(-xi) * g_plus))
            
    return beta

from scipy.stats import pearson3

def get_p3_theoretical_pwms(mu: float, sigma: float, skew: float, max_k: int = 8) -> np.ndarray:
    """
    Calculate theoretical PWMs for Pearson Type 3 distribution using numerical integration.
    beta_k = integral_0^1 x(F) F^k dF
    """
    beta = np.zeros(max_k + 1)
    
    for k in range(max_k + 1):
        # Integrand: Quantile(F) * F^k
        def integrand(F):
            if F <= 0: return 0.0
            if F >= 1: F = 0.99999999
            return pearson3.ppf(F, skew, loc=mu, scale=sigma) * (F**k)
            
        val, _ = integrate.quad(integrand, 0, 1, limit=100)
        beta[k] = val
        
    return beta

def get_normal_theoretical_pwms(mu: float, sigma: float, max_k: int = 8) -> np.ndarray:
    """
    Calculate theoretical PWMs for Normal distribution (used for LP3 in log-space).
    beta_k = mu/(k+1) + sigma * (some constant)
    For normal, L-moments are simpler:
    lambda_1 = mu
    lambda_2 = sigma / sqrt(pi)
    """
    # For now, we will use the relationship beta_k = integral mu + sigma*Phi^-1(F) F^k dF
    # This can be computed via lambda_r ratios or directly.
    # Actually, for LP3 we match LH-moments of log-flows to Pearson Type 3.
    # Pearson Type 3 PWMs are more complex. 
    # Let's revisit this in Phase 2.
    return np.zeros(max_k + 1)
