"""
Multiple Grubbs-Beck Test (MGBT) for Low Outlier Detection.
Ported and consolidated from experimental Python MGBT implementation.
Follows Cohn et al. (2013) and R package behavior.
"""

import numpy as np
import pandas as pd
from scipy import stats, integrate, special, optimize
from dataclasses import dataclass
from typing import List, Optional, Union, Tuple
import warnings

# --- Statistical Utilities (Ported from stats module) ---

def gtmoms(xsi: float, k: int) -> float:
    """
    Compute k-th moment of observations above threshold xsi for standard normal.
    """
    def H(x: float) -> float:
        """Hazard function: phi(x)/(1-Phi(x))"""
        return stats.norm.pdf(x) / (1 - stats.norm.cdf(x))

    if k == 0:
        return 1.0
    elif k == 1:
        return H(xsi)
    elif k > 1:
        return (k - 1) * gtmoms(xsi, k - 2) + H(xsi) * (xsi ** (k - 1))
    else:
        raise ValueError("Moment order k must be non-negative integer")

def cond_moms_chi2(n: int, r: int, xsi: float) -> np.ndarray:
    """
    Conditional moments for chi-squared related calculations.
    """
    mu1 = gtmoms(xsi, 1)
    mu2 = gtmoms(xsi, 2)
    p_threshold = stats.norm.cdf(xsi)
    variance_moment = mu2 - mu1**2
    covariance_matrix = V(n, r, p_threshold)
    variance_of_variance = covariance_matrix[1, 1]
    return np.array([variance_moment, variance_of_variance])

def V(n: int, r: int, qmin: float) -> np.ndarray:
    """
    Covariance matrix of sample mean (M) and sample variance (S2).
    """
    n2 = n - r
    if n2 <= 1:
        return np.zeros((2, 2))
    zr = stats.norm.ppf(qmin)
    E = np.array([gtmoms(zr, k) for k in range(1, 5)])
    cm = np.array([
        E[0],
        E[1] - E[0]**2,
        E[2] - 3*E[1]*E[0] + 2*E[0]**3,
        E[3] - 4*E[2]*E[0] + 6*E[1]*E[0]**2 - 3*E[0]**4
    ])
    var_m = (E[1] - E[0]**2) / n2
    cov_m_s2 = (E[2] - 3*E[0]*E[1] + 2*E[0]**3) / np.sqrt(n2 * (n2 - 1))
    var_s2 = (cm[3] - cm[1]**2) / n2 + 2 / ((n2 - 1) * n2) * cm[1]**2
    return np.array([[var_m, cov_m_s2], [cov_m_s2, var_s2]])

def EMS(n: int, r: int, qmin: float) -> np.ndarray:
    """
    Expected values of sample mean (M) and sample standard deviation (S).
    """
    zr = stats.norm.ppf(qmin)
    Em = gtmoms(zr, 1)
    mom_s2 = cond_moms_chi2(n, r, zr)
    alpha = mom_s2[0]**2 / mom_s2[1]
    beta = mom_s2[1] / mom_s2[0]
    Es = np.sqrt(beta) * np.exp(special.loggamma(alpha + 0.5) - special.loggamma(alpha))
    return np.array([Em, Es])

def VMS(n: int, r: int, qmin: float) -> np.ndarray:
    """
    Covariance matrix of sample mean (M) and sample standard deviation (S).
    """
    zr = stats.norm.ppf(qmin)
    E = np.array([gtmoms(zr, k) for k in range(1, 3)])
    ems_values = EMS(n, r, qmin)
    Es = ems_values[1]
    Es2 = E[1] - E[0]**2
    V2 = V(n, r, qmin)
    var_m = V2[0, 0]
    cov_m_s = V2[0, 1] / (2 * Es)
    var_s = Es2 - Es**2
    return np.array([[var_m, cov_m_s], [cov_m_s, var_s]])

# --- Core MGBT Logic (Ported from core/stats modules) ---

def peta(pzr: float, n: int, r: int, eta: float) -> float:
    """
    Integrand function for orthogonal p-value evaluation.
    """
    try:
        zr = stats.norm.ppf(stats.beta.ppf(pzr, a=r, b=n + 1 - r))
        qmin = stats.norm.cdf(zr)
        CV = VMS(n, r, qmin)
        EMp = EMS(n, r, qmin)
        lambda_coef = CV[0, 1] / CV[1, 1]
        etap = eta + lambda_coef
        mu_mp = EMp[0] - lambda_coef * EMp[1]
        sigma_mp = np.sqrt(CV[0, 0] - CV[0, 1]**2 / CV[1, 1])
        mom_s2 = cond_moms_chi2(n, r, zr)
        shape = mom_s2[0]**2 / mom_s2[1]
        df = 2 * shape
        ncp = (mu_mp - zr) / sigma_mp
        q = -(np.sqrt(mom_s2[0]) / sigma_mp) * etap
        return 1 - stats.nct.cdf(q, df=df, nc=ncp)
    except Exception:
        return 0.0

def kth_order_pvalue_ortho_t(n: int, r: int, eta: float) -> float:
    """
    Compute p-value for k-th order statistic using orthogonal evaluation.
    """
    val, _ = integrate.quad(peta, 0, 1, args=(n, r, eta), epsrel=1e-4)
    return val

@dataclass
class MGBTResult:
    klow: int
    low_outlier_threshold: Optional[float]
    outlier_indices: List[int]
    p_values: np.ndarray
    cleaned_flows: pd.Series

def detect_low_outliers(flows: pd.Series, alpha1: float = 0.01, alpha10: float = 0.10) -> MGBTResult:
    """
    Apply Multiple Grubbs-Beck Test to identify low outliers.
    Returns a result object containing the threshold and cleaned series.
    """
    Q = flows.values
    zt = np.sort(np.log10(np.maximum(1e-8, Q)))
    n = len(zt)
    n2 = n // 2
    p_values = np.full(n2, -99.0)
    w = np.full(n2, -99.0)
    
    j1, j2 = 0, 0
    for i in range(n2):
        # Index i is 0-based in Python, corresponds to i+1 in 1-based R
        r = i + 1
        tail_data = zt[i+1:]
        w[i] = (zt[i] - np.mean(tail_data)) / np.sqrt(np.var(tail_data, ddof=1))
        p_values[i] = kth_order_pvalue_ortho_t(n, r, w[i])
        
        if p_values[i] < alpha1:
            j1 = r
            j2 = r
        elif p_values[i] < alpha10 and j2 == r - 1:
            j2 = r
            
    # Map outliers back to original series
    sorted_indices = flows.index[np.argsort(flows.values)]
    outlier_years = sorted_indices[:j2].tolist()
    threshold = np.sort(Q)[j2] if j2 > 0 else None
    
    # Create cleaned series (remove outliers)
    cleaned_flows = flows.drop(outlier_years)
    
    return MGBTResult(
        klow=j2,
        low_outlier_threshold=threshold,
        outlier_indices=outlier_years,
        p_values=p_values,
        cleaned_flows=cleaned_flows
    )
