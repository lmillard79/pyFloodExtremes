import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import matplotlib.figure
import probscale
from scipy.stats import pearson3
from flood_ffa.gev.plots import cunnane_plotting_positions

def plot_trace(idata: az.InferenceData) -> matplotlib.figure.Figure:
    """Plots ArviZ trace plots for the LP3 parameters."""
    fig, axes = plt.subplots(3, 2, figsize=(10, 8))
    az.plot_trace(idata, var_names=["mu", "sigma", "skew"], axes=axes)
    fig.tight_layout()
    return fig

def plot_corner(idata: az.InferenceData) -> matplotlib.figure.Figure:
    """Plots a pair plot showing posterior correlations for LP3."""
    ax = az.plot_pair(idata, var_names=["mu", "sigma", "skew"], marginals=True)
    if isinstance(ax, np.ndarray):
        fig = ax[0, 0].figure
    else:
        fig = ax.figure
    return fig

def lp3_return_level(mu, sigma, skew, aep_pct):
    """
    Compute LP3 return level for a given AEP.
    Fitting is in log-space; output is back-transformed to m³/s.
    """
    p = aep_pct / 100.0
    log_rl = pearson3.ppf(1 - p, skew, loc=mu, scale=sigma)
    return np.exp(log_rl)

def plot_return_levels(idata: az.InferenceData, flows: pd.Series, aep_grid: np.ndarray = None) -> matplotlib.figure.Figure:
    """
    Plots the LP3 frequency curve on a probability scale using Australian conventions.
    """
    AEP_TICKS = [50, 20, 10, 5, 2, 1, 0.5, 0.2]
    if aep_grid is None:
        aep_grid = np.logspace(np.log10(0.2), np.log10(63), 300)
    
    post = idata.posterior
    mu = post["mu"].to_numpy().flatten()
    sigma = post["sigma"].to_numpy().flatten()
    skew = post["skew"].to_numpy().flatten()
    
    rl_samples = np.array([
        lp3_return_level(mu[i], sigma[i], skew[i], aep_grid)
        for i in range(len(mu))
    ])
    
    median = np.median(rl_samples, axis=0)
    hdi = az.hdi(rl_samples, hdi_prob=0.94)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # LP3 Plotting
    ax.plot(aep_grid, median, color='#00928f', lw=1.5, label='LP3 posterior median')
    ax.fill_between(aep_grid, hdi[:, 0], hdi[:, 1], alpha=0.25, color='#00928f', label='LP3 94% HDI')
    
    # Observed data
    aep_obs = cunnane_plotting_positions(flows.values)
    ax.scatter(aep_obs, flows.values, color='#485253', zorder=5, s=30, label='Observed AMS')
    
    # Formatting
    ax.set_xscale('prob')
    ax.set_xlim([63, 0.1])
    ax.set_xticks(AEP_TICKS)
    ax.set_xticklabels([f'{p}%' for p in AEP_TICKS])
    
    ax.set_xlabel('Annual Exceedance Probability (%)')
    ax.set_ylabel('Flow ($m^3/s$)')
    ax.set_title('LP3 Flood Frequency Curve')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='0.7')
    ax.legend()
    fig.tight_layout()
    
    return fig
