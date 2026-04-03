import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import matplotlib.figure

def plot_trace(idata: az.InferenceData) -> matplotlib.figure.Figure:
    """Plots ArviZ trace plots for all 7 TCEV parameters."""
    fig, axes = plt.subplots(7, 2, figsize=(10, 16))
    az.plot_trace(idata, var_names=["w", "mu1", "sigma1", "xi1", "mu2", "sigma2", "xi2"], axes=axes)
    fig.tight_layout()
    return fig

def plot_corner(idata: az.InferenceData) -> matplotlib.figure.Figure:
    """Plots a pair plot showing posterior correlations for TCEV."""
    ax = az.plot_pair(idata, var_names=["w", "mu1", "sigma1", "xi1", "mu2", "sigma2", "xi2"], marginals=True)
    if isinstance(ax, np.ndarray):
        fig = ax[0, 0].figure
    else:
        fig = ax.figure
    return fig

def gev_cdf_np(x, mu, sigma, xi):
    """Numpy implementation of GEV CDF for plotting."""
    z = (x - mu) / sigma
    eps = 1e-6
    cdf = np.zeros_like(z)
    if abs(xi) < eps:
        cdf = np.exp(-np.exp(-z))
    else:
        cond = 1 + xi * z
        valid = cond > 0
        cdf[valid] = np.exp(-(cond[valid] ** (-1/xi)))
        if xi < 0:
            cdf[~valid & (z > 0)] = 1.0
    return cdf

def plot_return_levels(idata: az.InferenceData, flows: pd.Series, return_periods: list[float] = None) -> matplotlib.figure.Figure:
    """
    Plots the mixture return level curve with 94% HDI uncertainty band.
    Solves the implicit return level equation numerically via CDF interpolation.
    """
    if return_periods is None:
        return_periods = np.logspace(0.1, 3, 100)
        
    T = np.array(return_periods)
    p_target = 1 - 1 / T
    
    post = idata.posterior
    w = post["w"].to_numpy().flatten()
    mu1 = post["mu1"].to_numpy().flatten()
    sigma1 = post["sigma1"].to_numpy().flatten()
    xi1 = post["xi1"].to_numpy().flatten()
    mu2 = post["mu2"].to_numpy().flatten()
    sigma2 = post["sigma2"].to_numpy().flatten()
    xi2 = post["xi2"].to_numpy().flatten()
    
    n_samples = len(w)
    
    # Dense grid of x values to evaluate the CDF
    x_grid = np.linspace(flows.min() * 0.1, flows.max() * 5, 3000)
    y_p_all = np.zeros((n_samples, len(T)))
    
    for i in range(n_samples):
        cdf1 = gev_cdf_np(x_grid, mu1[i], sigma1[i], xi1[i])
        cdf2 = gev_cdf_np(x_grid, mu2[i], sigma2[i], xi2[i])
        
        mix_cdf = (1 - w[i]) * cdf1 + w[i] * cdf2
        
        # Interpolate to find x(T). mix_cdf is monotonically increasing.
        y_p_all[i, :] = np.interp(p_target, mix_cdf, x_grid)
        
    y_median = np.median(y_p_all, axis=0)
    y_hdi = az.hdi(y_p_all, hdi_prob=0.94)
    
    n = len(flows)
    sorted_flows = np.sort(flows)[::-1]
    ranks = np.arange(1, n + 1)
    obs_T = (n + 1) / ranks
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(T, y_median, color="C2", label="Posterior Median (TCEV)")
    ax.fill_between(T, y_hdi[:, 0], y_hdi[:, 1], color="C2", alpha=0.3, label="94% HDI")
    ax.scatter(obs_T, sorted_flows, color="black", label="Observed (Weibull PP)", zorder=5)
    
    ax.set_xscale("log")
    ax.set_xlabel("Return Period (years)")
    ax.set_ylabel("Flow ($m^3/s$)")
    ax.set_title("TCEV Return Levels")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.7)
    
    return fig

def gev_logpdf_np(x, mu, sigma, xi):
    """Numpy implementation of GEV logPDF."""
    z = (x - mu) / sigma
    eps = 1e-6
    logp = np.full_like(z, -np.inf, dtype=float)
    if abs(xi) < eps:
        logp = -np.log(sigma) - z - np.exp(-z)
    else:
        cond = 1 + xi * z
        valid = cond > 0
        if np.any(valid):
            t = cond[valid] ** (-1/xi)
            logp[valid] = -np.log(sigma) - (1 + 1/xi) * np.log(cond[valid]) - t
    return logp

def plot_component_separation(idata: az.InferenceData, flows: pd.Series) -> matplotlib.figure.Figure:
    """
    Plots the posterior probability that each observation belongs to component 2.
    Highlights extraordinary floods (like the 2021 outlier).
    """
    post = idata.posterior
    w = post["w"].to_numpy().flatten()
    mu1 = post["mu1"].to_numpy().flatten()
    sigma1 = post["sigma1"].to_numpy().flatten()
    xi1 = post["xi1"].to_numpy().flatten()
    mu2 = post["mu2"].to_numpy().flatten()
    sigma2 = post["sigma2"].to_numpy().flatten()
    xi2 = post["xi2"].to_numpy().flatten()
    
    n_samples = len(w)
    n_obs = len(flows)
    x = flows.values
    
    p2_prob = np.zeros((n_samples, n_obs))
    
    for i in range(n_samples):
        logp1 = gev_logpdf_np(x, mu1[i], sigma1[i], xi1[i])
        logp2 = gev_logpdf_np(x, mu2[i], sigma2[i], xi2[i])
        
        log_joint1 = np.log(1 - w[i]) + logp1
        log_joint2 = np.log(w[i]) + logp2
        
        max_log = np.maximum(log_joint1, log_joint2)
        p1 = np.exp(log_joint1 - max_log)
        p2 = np.exp(log_joint2 - max_log)
        
        p2_prob[i, :] = p2 / (p1 + p2)
        
    median_prob = np.median(p2_prob, axis=0)
    hdi_prob = az.hdi(p2_prob, hdi_prob=0.94)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    years = flows.index
    ax.plot(years, median_prob, color="C3", marker="o", linestyle="-", label="Median P(C=2 | X)")
    ax.fill_between(years, hdi_prob[:, 0], hdi_prob[:, 1], color="C3", alpha=0.3, label="94% HDI")
    
    ax.set_xlabel("Year")
    ax.set_ylabel("Posterior Probability of Component 2")
    ax.set_title("TCEV Component Separation")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.7)
    
    return fig
