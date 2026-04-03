import numpy as np
import pandas as pd
import arviz as az
import matplotlib.pyplot as plt
import matplotlib.figure
import probscale
from flood_ffa.gev.plots import cunnane_plotting_positions, gev_return_level
from flood_ffa.lp3.plots import lp3_return_level
from flood_ffa.tcev.plots import tcev_return_level

def plot_comparison(
    gev_idata: az.InferenceData,
    lp3_idata: az.InferenceData,
    tcev_idata: az.InferenceData,
    flows: pd.Series,
    aep_grid: np.ndarray = None
) -> matplotlib.figure.Figure:
    """
    Plots a side-by-side comparison of GEV, LP3, and TCEV frequency curves
    using Australian plotting conventions.
    """
    AEP_TICKS = [50, 20, 10, 5, 2, 1, 0.5, 0.2]
    if aep_grid is None:
        aep_grid = np.logspace(np.log10(0.2), np.log10(63), 300)
        
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Colours from skill document
    DIST_COLORS = {
        'gev':  '#1e4164',  # Blue
        'lp3':  '#00928f',  # Teal
        'tcev': '#8dc63f',  # Green
        'obs':  '#485253',  # Charcoal
    }

    # 1. GEV
    post_gev = gev_idata.posterior
    mu_gev = post_gev["mu"].to_numpy().flatten()
    sigma_gev = post_gev["sigma"].to_numpy().flatten()
    xi_gev = post_gev["xi"].to_numpy().flatten()
    
    rl_gev = np.array([gev_return_level(mu_gev[i], sigma_gev[i], xi_gev[i], aep_grid) for i in range(len(mu_gev))])
    gev_median = np.median(rl_gev, axis=0)
    gev_hdi = az.hdi(rl_gev, hdi_prob=0.94)
    
    ax.plot(aep_grid, gev_median, color=DIST_COLORS['gev'], label="GEV Median")
    ax.fill_between(aep_grid, gev_hdi[:, 0], gev_hdi[:, 1], color=DIST_COLORS['gev'], alpha=0.1)
    
    # 2. LP3
    post_lp3 = lp3_idata.posterior
    mu_lp3 = post_lp3["mu"].to_numpy().flatten()
    sigma_lp3 = post_lp3["sigma"].to_numpy().flatten()
    skew_lp3 = post_lp3["skew"].to_numpy().flatten()
    
    rl_lp3 = np.array([lp3_return_level(mu_lp3[i], sigma_lp3[i], skew_lp3[i], aep_grid) for i in range(len(mu_lp3))])
    lp3_median = np.median(rl_lp3, axis=0)
    lp3_hdi = az.hdi(rl_lp3, hdi_prob=0.94)
    
    ax.plot(aep_grid, lp3_median, color=DIST_COLORS['lp3'], label="LP3 Median")
    ax.fill_between(aep_grid, lp3_hdi[:, 0], lp3_hdi[:, 1], color=DIST_COLORS['lp3'], alpha=0.1)
    
    # 3. TCEV
    post_tcev = tcev_idata.posterior
    w_tcev = post_tcev["w"].to_numpy().flatten()
    mu1_tcev = post_tcev["mu1"].to_numpy().flatten()
    sigma1_tcev = post_tcev["sigma1"].to_numpy().flatten()
    xi1_tcev = post_tcev["xi1"].to_numpy().flatten()
    mu2_tcev = post_tcev["mu2"].to_numpy().flatten()
    sigma2_tcev = post_tcev["sigma2"].to_numpy().flatten()
    xi2_tcev = post_tcev["xi2"].to_numpy().flatten()
    
    x_grid = np.linspace(flows.min() * 0.1, flows.max() * 6, 4000)
    rl_tcev = np.array([
        tcev_return_level(w_tcev[i], mu1_tcev[i], sigma1_tcev[i], xi1_tcev[i], 
                          mu2_tcev[i], sigma2_tcev[i], xi2_tcev[i], aep_grid, x_grid) 
        for i in range(len(w_tcev))
    ])
    tcev_median = np.median(rl_tcev, axis=0)
    tcev_hdi = az.hdi(rl_tcev, hdi_prob=0.94)
    
    ax.plot(aep_grid, tcev_median, color=DIST_COLORS['tcev'], label="TCEV Median")
    ax.fill_between(aep_grid, tcev_hdi[:, 0], tcev_hdi[:, 1], color=DIST_COLORS['tcev'], alpha=0.1)
    
    # 4. Observed
    aep_obs = cunnane_plotting_positions(flows.values)
    ax.scatter(aep_obs, flows.values, color=DIST_COLORS['obs'], marker='o', s=30, label="Observed AMS", zorder=10)
    
    # Formatting
    ax.set_xscale('prob')
    ax.set_xlim([63, 0.1])
    ax.set_xticks(AEP_TICKS)
    ax.set_xticklabels([f'{p}%' for p in AEP_TICKS])
    
    ax.set_xlabel('Annual Exceedance Probability (%)')
    ax.set_ylabel('Flow ($m^3/s$)')
    ax.set_title('Flood Frequency Comparison: GEV vs LP3 vs TCEV')
    ax.legend(loc="upper left")
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='0.7')
    
    # Cap y-limit
    all_medians = np.concatenate([gev_median, lp3_median, tcev_median])
    ax.set_ylim(bottom=0, top=np.max(all_medians) * 1.3)
    
    fig.tight_layout()
    return fig
