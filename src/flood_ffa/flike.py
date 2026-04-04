"""
FLIKE Emulator: Orchestrates the full FFA workflow using LH-moments.
"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from flood_ffa.preprocessing.mgbt import detect_low_outliers
from flood_ffa.gev.fit_lh import fit_gev_lh, get_gev_quantile
from flood_ffa.lp3.fit_lh import fit_lp3_lh, get_lp3_quantile
from flood_ffa.stats.bootstrap import run_parametric_bootstrap

class FLIKE:
    """
    Emulator for TUFLOW FLIKE workflow.
    """
    def __init__(self, model_type: str = "gev"):
        if model_type.lower() not in ["gev", "lp3"]:
            raise ValueError("Model type must be 'gev' or 'lp3'")
        self.model_type = model_type.lower()
        self.fit_results = {}
        self.bootstrap_results = None
        self.aep_grid = np.logspace(np.log10(0.01), np.log10(99), 100)
        
    def run(self, flows: pd.Series, shift: Optional[int] = None, n_sim: int = 500) -> Dict[str, Any]:
        """
        Execute the full FLIKE workflow.
        """
        # 1. MGBT Outlier Detection
        print("Step 1: Running Multiple Grubbs-Beck Test...")
        mgbt_res = detect_low_outliers(flows)
        self.mgbt_result = mgbt_res
        if mgbt_res.klow > 0:
            print(f"  Detected {mgbt_res.klow} low outliers below {mgbt_res.low_outlier_threshold:.2f} m3/s")
        else:
            print("  No low outliers detected.")
            
        working_flows = mgbt_res.cleaned_flows.values
        
        # 2. Optimized Shift Search (if shift is None)
        best_fit = None
        if shift is None:
            print("Step 2: Searching for Optimized Shift (h=0 to 4)...")
            # In this emulator, we'll fit all shifts and pick the smallest h 
            # that has reasonable parameters (sigma > 0). 
            # Real FLIKE uses Z4 test, here we'll provide the results for all.
            fits = {}
            for h in range(5):
                if self.model_type == "gev":
                    res = fit_gev_lh(working_flows, shift=h)
                else:
                    res = fit_lp3_lh(working_flows, shift=h)
                
                if res["success"]:
                    fits[h] = res
                    if best_fit is None: # Default to smallest successful shift
                        best_fit = res
            
            self.all_fits = fits
            if best_fit:
                print(f"  Selected shift h={best_fit['shift']}")
            else:
                raise RuntimeError("Failed to fit model for any shift.")
        else:
            print(f"Step 2: Fitting model with manual shift h={shift}...")
            if self.model_type == "gev":
                best_fit = fit_gev_lh(working_flows, shift=shift)
            else:
                best_fit = fit_lp3_lh(working_flows, shift=shift)
            if not best_fit["success"]:
                raise RuntimeError(f"Fit failed for shift {shift}: {best_fit.get('message')}")

        self.best_fit = best_fit
        
        # 3. Parametric Bootstrap
        print(f"Step 3: Running Parametric Bootstrap (n_sim={n_sim}) for uncertainty...")
        if self.model_type == "gev":
            self.bootstrap_quantiles = run_parametric_bootstrap(
                fit_gev_lh, get_gev_quantile, best_fit, len(working_flows), self.aep_grid, n_sim=n_sim, dist_type="gev"
            )
        else:
            self.bootstrap_quantiles = run_parametric_bootstrap(
                fit_lp3_lh, get_lp3_quantile, best_fit, len(working_flows), self.aep_grid, n_sim=n_sim, dist_type="lp3"
            )
            
        # 4. Summarise results
        results = self._generate_report(flows)
        return results

    def _generate_report(self, flows: pd.Series) -> Dict[str, Any]:
        """
        Generate summary quantiles and parameters.
        """
        # Calculate median quantiles and 90% confidence limits (standard FLIKE reporting)
        q_median = np.nanmedian(self.bootstrap_quantiles, axis=0)
        q_lower = np.nanpercentile(self.bootstrap_quantiles, 5, axis=0)
        q_upper = np.nanpercentile(self.bootstrap_quantiles, 95, axis=0)
        
        # Standard AEPs for report
        std_aeps = [10, 5, 2, 1, 0.5, 0.2]
        std_results = []
        
        fit_func = get_gev_quantile if self.model_type == "gev" else get_lp3_quantile
        params = [self.best_fit["mu"], self.best_fit["sigma"], 
                  self.best_fit["xi"] if self.model_type == "gev" else self.best_fit["skew"]]
        
        for aep in std_aeps:
            val = fit_func(*params, aep)
            # Find closest index in aep_grid
            idx = np.argmin(np.abs(self.aep_grid - aep))
            std_results.append({
                "AEP (%)": aep,
                "Expected (m3/s)": round(val, 1),
                "5% Limit": round(q_lower[idx], 1),
                "95% Limit": round(q_upper[idx], 1)
            })
            
        report = {
            "model": self.model_type.upper(),
            "shift": self.best_fit["shift"],
            "parameters": self.best_fit,
            "quantiles": pd.DataFrame(std_results),
            "mgbt": self.mgbt_result
        }
        self.report = report
        return report
