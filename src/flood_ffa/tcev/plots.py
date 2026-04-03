import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import matplotlib.figure
import probscale
from flood_ffa.gev.plots import cunnane_plotting_positions, gev_return_level, gev_logpdf_np

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

def tcev_return_level(w, mu1, sigma1, xi1, mu2, sigma2, xi2, aep_pct, x_grid):
    """
    Compute TCEV return level for a given AEP via numerical inversion.
    """
    p_target = 1 - aep_pct / 100.0
    
    cdf1 = gev_cdf_np(x_grid, mu1, sigma1, xi1)
    cdf2 = gev_cdf_np(x_grid, mu2, sigma2, xi2)
    
    mix_cdf = (1 - w) * cdf1 + w * cdf2
    
    # Interpolate to find x(T). mix_cdf is monotonically increasing.
    return np.interp(p_target, mix_cdf, x_grid)

def plot_return_levels(idata: az.InferenceData, flows: pd.Series, aep_grid: np.ndarray = None) -> matplotlib.figure.Figure:
    """
    Plots the TCEV mixture frequency curve on a probability scale using Australian conventions.
    """
    AEP_TICKS = [50, 20, 10, 5, 2, 1, 0.5, 0.2]
    if aep_grid is None:
        aep_grid = np.logspace(np.log10(0.2), np.log10(63), 300)
        
    post = idata.posterior
    w = post["w"].to_numpy().flatten()
    mu1 = post["mu1"].to_numpy().flatten()
    sigma1 = post["sigma1"].to_numpy().flatten()
    xi1 = post["xi1"].to_numpy().flatten()
    mu2 = post["mu2"].to_numpy().flatten()
    sigma2 = post["sigma2"].to_numpy().flatten()
    xi2 = post["xi2"].to_numpy().flatten()
    
    n_samples = len(w)
    x_grid = np.linspace(flows.min() * 0.1, flows.max() * 5, 3000)
    
    rl_samples = np.array([
        tcev_return_level(w[i], mu1[i], sigma1[i], xi1[i], mu2[i], sigma2[i], xi2[i], aep_grid, x_grid)
        for i in range(n_samples)
    ])
        
    median = np.median(rl_samples, axis=0)
    
    # Reshape to (chain, draw, shape) to avoid ArviZ future warnings
    n_chains = idata.posterior.dims['chain']
    n_draws = idata.posterior.dims['draw']
    rl_reshaped = rl_samples.reshape((n_chains, n_draws, len(aep_grid)))
    hdi = az.hdi(rl_reshaped, hdi_prob=0.94)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # TCEV Plotting
    ax.plot(aep_grid, median, color='#8dc63f', lw=1.5, label='TCEV posterior median')
    ax.fill_between(aep_grid, hdi[:, 0], hdi[:, 1], alpha=0.25, color='#8dc63f', label='TCEV 94% HDI')

    # Observed data
    aep_obs = cunnane_plotting_positions(flows.values)
    ax.scatter(aep_obs, flows.values, color='#485253', zorder=5, s=30, label='Observed AMS')

    # Formatting
    ax.set_xscale('prob')
    ax.set_yscale('log')
    ax.set_xlim([63, 0.1])
    ax.set_xticks(AEP_TICKS)
    ax.set_xticklabels([f'{p}%' for p in AEP_TICKS])
    
    ax.set_xlabel('Annual Exceedance Probability (%)')
    ax.set_ylabel('Flow ($m^3/s$) [Log Scale]')
    ax.set_title('TCEV Flood Frequency Curve')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='0.7')
    ax.legend()
    fig.tight_layout()
    
    return fig

def plot_component_separation(idata: az.InferenceData, flows: pd.Series) -> matplotlib.figure.Figure:
    """
    Plots the posterior probability that each observation belongs to component 2.
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
    
    # Reshape to (chain, draw, shape) to avoid ArviZ future warnings
    n_chains = idata.posterior.dims['chain']
    n_draws = idata.posterior.dims['draw']
    p2_reshaped = p2_prob.reshape((n_chains, n_draws, n_obs))
    hdi_prob = az.hdi(p2_reshaped, hdi_prob=0.94)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    years = flows.index
    ax.plot(years, median_prob, color='#8dc63f', marker='o', linestyle='-', label='Median P(C=2 | X)')
    ax.fill_between(years, hdi_prob[:, 0], hdi_prob[:, 1], color='#8dc63f', alpha=0.3, label='94% HDI')
    
    ax.set_xlabel('Year')
    ax.set_ylabel('Posterior Probability of Component 2')
    ax.set_title('TCEV Component Separation')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    
    return fig
