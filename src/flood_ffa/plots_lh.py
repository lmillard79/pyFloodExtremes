"""
Plotting utilities for LH-moments and FLIKE emulator results.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.figure
import probscale
from flood_ffa.gev.plots import cunnane_plotting_positions
from flood_ffa.gev.fit_lh import get_gev_quantile
from flood_ffa.lp3.fit_lh import get_lp3_quantile

def plot_flike_results(flike_obj, flows: pd.Series) -> matplotlib.figure.Figure:
    """
    Generate a FLIKE-style probability plot.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    aep_grid = flike_obj.aep_grid
    
    # 1. Fitted Curve
    fit = flike_obj.best_fit
    if flike_obj.model_type == "gev":
        y_fit = [get_gev_quantile(fit["mu"], fit["sigma"], fit["xi"], aep) for aep in aep_grid]
        label = f"GEV (h={fit['shift']})"
        color = "#1e4164"
    else:
        y_fit = [get_lp3_quantile(fit["mu"], fit["sigma"], fit["skew"], aep) for aep in aep_grid]
        label = f"LP3 (h={fit['shift']})"
        color = "#00928f"
        
    ax.plot(aep_grid, y_fit, color=color, lw=2, label=f"Fitted {label}")
    
    # 2. Confidence Limits (from bootstrap)
    q_lower = np.nanpercentile(flike_obj.bootstrap_quantiles, 5, axis=0)
    q_upper = np.nanpercentile(flike_obj.bootstrap_quantiles, 95, axis=0)
    
    ax.fill_between(aep_grid, q_lower, q_upper, color=color, alpha=0.15, label="90% Confidence Limits")
    
    # 3. Observed Data
    # Identify censored vs retained
    mgbt = flike_obj.mgbt_result
    aep_obs = cunnane_plotting_positions(flows.values)
    
    # All observed
    ax.scatter(aep_obs, flows.values, color="#485253", alpha=0.3, label="Observed (all)", s=20)
    
    # Retained (if outliers were found)
    if mgbt.klow > 0:
        retained_mask = ~flows.index.isin(mgbt.outlier_indices)
        ax.scatter(aep_obs[retained_mask], flows.values[retained_mask], 
                   color="#485253", marker='o', s=40, label="Retained observations")
        # Highlight censored
        ax.scatter(aep_obs[~retained_mask], flows.values[~retained_mask], 
                   color="red", marker='x', s=40, label="Censored (Low Outliers)")
    
    # Formatting
    ax.set_xscale('prob')
    ax.set_yscale('log')
    ax.set_xlim([63, 0.05]) # Show down to 0.05% AEP
    
    AEP_TICKS = [50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1, 0.05]
    ax.set_xticks(AEP_TICKS)
    ax.set_xticklabels([f'{p}%' for p in AEP_TICKS])
    
    ax.set_xlabel('Annual Exceedance Probability (%)')
    ax.set_ylabel('Flow ($m^3/s$) [Log Scale]')
    ax.set_title(f'FLIKE Emulator: {label} Flood Frequency Curve')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, color='0.7')
    ax.legend()
    
    fig.tight_layout()
    return fig
