import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import matplotlib.figure
from scipy.stats import pearson3

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

def plot_return_levels(idata: az.InferenceData, flows: pd.Series, return_periods: list[float] = None) -> matplotlib.figure.Figure:
    """
    Plots the return level curve with 94% HDI uncertainty band.
    Plots observed data using Weibull plotting positions.
    Return levels are calculated in log-space and exponentiated.
    """
    if return_periods is None:
        return_periods = np.logspace(0.1, 3, 100)
        
    T = np.array(return_periods)
    p = 1 - 1 / T
    
    post = idata.posterior
    # Stack chains and draws
    mu = post["mu"].to_numpy().flatten()
    sigma = post["sigma"].to_numpy().flatten()
    skew = post["skew"].to_numpy().flatten()
    
    y_p_all = np.zeros((len(mu), len(T)))
    
    for i in range(len(mu)):
        # Calculate return levels in log space using scipy.stats.pearson3
        # scipy param skew is our skew parameter, loc is mu, scale is sigma
        log_quantiles = pearson3.ppf(p, skew[i], loc=mu[i], scale=sigma[i])
        # Back-transform to normal space
        y_p_all[i, :] = np.exp(log_quantiles)
            
    # Calculate median
    y_median = np.median(y_p_all, axis=0)
    
    # Calculate 94% HDI using ArviZ
    y_hdi = az.hdi(y_p_all, hdi_prob=0.94)
    
    # Calculate Weibull plotting positions for observed data
    n = len(flows)
    sorted_flows = np.sort(flows)[::-1]
    ranks = np.arange(1, n + 1)
    obs_T = (n + 1) / ranks
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(T, y_median, color="C1", label="Posterior Median (LP3)")
    ax.fill_between(T, y_hdi[:, 0], y_hdi[:, 1], color="C1", alpha=0.3, label="94% HDI")
    ax.scatter(obs_T, sorted_flows, color="black", label="Observed (Weibull PP)", zorder=5)
    
    ax.set_xscale("log")
    ax.set_xlabel("Return Period (years)")
    ax.set_ylabel("Flow ($m^3/s$)")
    ax.set_title("LP3 Return Levels")
    ax.legend()
    ax.grid(True, which="both", linestyle="--", alpha=0.7)
    
    return fig
