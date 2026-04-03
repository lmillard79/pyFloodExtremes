import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import matplotlib.figure
from flood_ffa.tcev.plots import gev_cdf_np
from scipy.stats import pearson3

def plot_comparison(
    gev_idata: az.InferenceData,
    lp3_idata: az.InferenceData,
    tcev_idata: az.InferenceData,
    flows: pd.Series,
    return_periods: list[float] = None
) -> matplotlib.figure.Figure:
    """
    Plots a side-by-side comparison of GEV, LP3, and TCEV return levels.
    """
    if return_periods is None:
        # Extend up to ~3000 years to clearly show divergence in the upper tail
        return_periods = np.logspace(0.1, 3.5, 150)
        
    T = np.array(return_periods)
    p_target = 1 - 1 / T
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 1. GEV
    post_gev = gev_idata.posterior
    mu_gev = post_gev["mu"].to_numpy().flatten()
    sigma_gev = post_gev["sigma"].to_numpy().flatten()
    xi_gev = post_gev["xi"].to_numpy().flatten()
    
    y_gev = np.zeros((len(mu_gev), len(T)))
    eps = 1e-6
    for i in range(len(mu_gev)):
        if abs(xi_gev[i]) < eps:
            y_gev[i, :] = mu_gev[i] - sigma_gev[i] * np.log(-np.log(p_target))
        else:
            y_gev[i, :] = mu_gev[i] + (sigma_gev[i] / xi_gev[i]) * (np.power(-np.log(p_target), -xi_gev[i]) - 1)
            
    gev_median = np.median(y_gev, axis=0)
    gev_hdi = az.hdi(y_gev, hdi_prob=0.94)
    
    ax.plot(T, gev_median, color="C0", label="GEV Median")
    ax.fill_between(T, gev_hdi[:, 0], gev_hdi[:, 1], color="C0", alpha=0.15)
    
    # 2. LP3
    post_lp3 = lp3_idata.posterior
    mu_lp3 = post_lp3["mu"].to_numpy().flatten()
    sigma_lp3 = post_lp3["sigma"].to_numpy().flatten()
    skew_lp3 = post_lp3["skew"].to_numpy().flatten()
    
    y_lp3 = np.zeros((len(mu_lp3), len(T)))
    for i in range(len(mu_lp3)):
        log_quantiles = pearson3.ppf(p_target, skew_lp3[i], loc=mu_lp3[i], scale=sigma_lp3[i])
        y_lp3[i, :] = np.exp(log_quantiles)
        
    lp3_median = np.median(y_lp3, axis=0)
    lp3_hdi = az.hdi(y_lp3, hdi_prob=0.94)
    
    ax.plot(T, lp3_median, color="C1", label="LP3 Median")
    ax.fill_between(T, lp3_hdi[:, 0], lp3_hdi[:, 1], color="C1", alpha=0.15)
    
    # 3. TCEV
    post_tcev = tcev_idata.posterior
    w_tcev = post_tcev["w"].to_numpy().flatten()
    mu1_tcev = post_tcev["mu1"].to_numpy().flatten()
    sigma1_tcev = post_tcev["sigma1"].to_numpy().flatten()
    xi1_tcev = post_tcev["xi1"].to_numpy().flatten()
    mu2_tcev = post_tcev["mu2"].to_numpy().flatten()
    sigma2_tcev = post_tcev["sigma2"].to_numpy().flatten()
    xi2_tcev = post_tcev["xi2"].to_numpy().flatten()
    
    x_grid = np.linspace(flows.min() * 0.1, max(np.max(gev_hdi), flows.max()) * 2, 5000)
    y_tcev = np.zeros((len(w_tcev), len(T)))
    for i in range(len(w_tcev)):
        cdf1 = gev_cdf_np(x_grid, mu1_tcev[i], sigma1_tcev[i], xi1_tcev[i])
        cdf2 = gev_cdf_np(x_grid, mu2_tcev[i], sigma2_tcev[i], xi2_tcev[i])
        mix_cdf = (1 - w_tcev[i]) * cdf1 + w_tcev[i] * cdf2
        y_tcev[i, :] = np.interp(p_target, mix_cdf, x_grid)
        
    tcev_median = np.median(y_tcev, axis=0)
    tcev_hdi = az.hdi(y_tcev, hdi_prob=0.94)
    
    ax.plot(T, tcev_median, color="C2", label="TCEV Median")
    ax.fill_between(T, tcev_hdi[:, 0], tcev_hdi[:, 1], color="C2", alpha=0.15)
    
    # 4. Observed
    n = len(flows)
    sorted_flows = np.sort(flows)[::-1]
    ranks = np.arange(1, n + 1)
    obs_T = (n + 1) / ranks
    
    ax.scatter(obs_T, sorted_flows, color="black", marker="x", label="Observed", zorder=10)
    
    ax.set_xscale("log")
    ax.set_xlabel("Return Period (years)")
    ax.set_ylabel("Flow ($m^3/s$)")
    ax.set_title("Return Level Comparison: GEV vs LP3 vs TCEV")
    ax.legend(loc="upper left")
    ax.grid(True, which="both", linestyle="--", alpha=0.7)
    
    # Cap y-limit to avoid extreme upper tail distortions squeezing out the detail
    max_plot_y = max(np.max(tcev_median) * 1.5, np.max(gev_median) * 1.5, np.max(lp3_median) * 1.5, flows.max() * 1.5)
    ax.set_ylim(bottom=0, top=max_plot_y)
    
    return fig
