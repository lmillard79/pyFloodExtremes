import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import matplotlib.figure
import probscale
from scipy.stats import genextreme

def plot_trace(idata: az.InferenceData) -> matplotlib.figure.Figure:
    """Plots ArviZ trace plots for the GEV parameters."""
    fig, axes = plt.subplots(3, 2, figsize=(10, 8))
    az.plot_trace(idata, var_names=["mu", "sigma", "xi"], axes=axes)
    fig.tight_layout()
    return fig

def plot_corner(idata: az.InferenceData) -> matplotlib.figure.Figure:
    """Plots a pair plot showing posterior correlations."""
    ax = az.plot_pair(idata, var_names=["mu", "sigma", "xi"], marginals=True)
    if isinstance(ax, np.ndarray):
        fig = ax[0, 0].figure
    else:
        fig = ax.figure
    return fig

def cunnane_plotting_positions(flows: np.ndarray) -> np.ndarray:
    """
    Compute Cunnane plotting positions for observed annual maxima.
    Returns AEP values in percent (0-100).
    Ranks observations such that the largest flow has the smallest AEP.
    """
    n = len(flows)
    # Ranks 1..n (1 is smallest)
    ranks = np.argsort(np.argsort(flows)) + 1
    # Annual Exceedance Probability (AEP) in percent
    aep = (1 - (ranks - 0.4) / (n + 0.2)) * 100
    return aep

def gev_return_level(mu, sigma, xi, aep_pct):
    """
    Compute GEV return level for a given AEP using scipy convention.
    """
    p = aep_pct / 100.0
    # scipy genextreme uses shape convention: sign of xi is negated vs standard
    return genextreme.ppf(1 - p, c=-xi, loc=mu, scale=sigma)

def plot_return_levels(idata: az.InferenceData, flows: pd.Series, aep_grid: np.ndarray = None) -> matplotlib.figure.Figure:
    """
    Plots the GEV frequency curve on a probability scale using Australian conventions.
    """
    AEP_TICKS = [50, 20, 10, 5, 2, 1, 0.5, 0.2]
    if aep_grid is None:
        aep_grid = np.logspace(np.log10(0.2), np.log10(63), 300)
    
    post = idata.posterior
    mu = post["mu"].to_numpy().flatten()
    sigma = post["sigma"].to_numpy().flatten()
    xi = post["xi"].to_numpy().flatten()
    
    # Calculate return levels for all posterior samples
    rl_samples = np.array([
        gev_return_level(mu[i], sigma[i], xi[i], aep_grid)
        for i in range(len(mu))
    ])
    
    median = np.median(rl_samples, axis=0)
    
    # Reshape to (chain, draw, shape) to avoid ArviZ future warnings
    n_chains = idata.posterior.sizes['chain']
    n_draws = idata.posterior.sizes['draw']
    rl_reshaped = rl_samples.reshape((n_chains, n_draws, len(aep_grid)))
    hdi = az.hdi(rl_reshaped, hdi_prob=0.94)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # GEV Plotting
    ax.plot(aep_grid, median, color='#1e4164', lw=1.5, label='GEV posterior median')
    ax.fill_between(aep_grid, hdi[:, 0], hdi[:, 1], alpha=0.25, color='#1e4164', label='GEV 94% HDI')
    
    # Observed data
    aep_obs = cunnane_plotting_positions(flows.values)
    ax.scatter(aep_obs, flows.values, color='#485253', zorder=5, s=30, label='Observed AMS')
    
    # Formatting
    ax.set_xscale('prob')
    ax.set_yscale('log')
    ax.set_xlim([63, 0.1]) # High AEP on left, low on right
    ax.set_xticks(AEP_TICKS)
    ax.set_xticklabels([f'{p}%' for p in AEP_TICKS])
    
    ax.set_xlabel('Annual Exceedance Probability (%)')
    ax.set_ylabel('Flow ($m^3/s$) [Log Scale]')
    ax.set_title('GEV Flood Frequency Curve')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='0.7')
    ax.legend()
    fig.tight_layout()
    
    return fig

def gev_logpdf_np(x, mu, sigma, xi):
    """Numpy implementation of GEV logPDF for component separation plots."""
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
