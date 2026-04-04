"""Smoke tests for core Bayesian fit functions."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import genextreme

from flood_ffa import fit_gev, fit_lp3
from flood_ffa.gev.fit_lh import get_gev_quantile
from flood_ffa.lp3.fit_lh import get_lp3_quantile


class TestFitGEV:
    """Smoke tests for GEV fitting function."""

    def test_fit_gev_returns_idata_with_expected_variables(self):
        """Test that fit_gev returns InferenceData with mu, sigma, xi."""
        # Generate synthetic GEV sample
        np.random.seed(42)
        true_mu, true_sigma, true_xi = 1000.0, 300.0, 0.1
        # Scipy uses c = -xi convention
        sample = genextreme.rvs(c=-true_xi, loc=true_mu, scale=true_sigma, size=30)
        flows = pd.Series(sample)

        # Fit with reduced draws for test speed
        idata = fit_gev(flows, draws=500, tune=500)

        # Assert expected variables present
        assert "mu" in idata.posterior, "Posterior should contain 'mu'"
        assert "sigma" in idata.posterior, "Posterior should contain 'sigma'"
        assert "xi" in idata.posterior, "Posterior should contain 'xi'"

    def test_fit_gev_1pct_aep_quantile_in_plausible_range(self):
        """Test that 1% AEP quantile is within physically plausible range."""
        np.random.seed(42)
        true_mu, true_sigma, true_xi = 1000.0, 300.0, 0.1
        sample = genextreme.rvs(c=-true_xi, loc=true_mu, scale=true_sigma, size=30)
        flows = pd.Series(sample)

        idata = fit_gev(flows, draws=500, tune=500)

        # Calculate posterior median 1% AEP quantile
        mu_samples = idata.posterior["mu"].values.flatten()
        sigma_samples = idata.posterior["sigma"].values.flatten()
        xi_samples = idata.posterior["xi"].values.flatten()

        quantiles_1pct = [
            get_gev_quantile(mu, sigma, xi, 1.0)
            for mu, sigma, xi in zip(mu_samples, sigma_samples, xi_samples)
        ]
        median_q1pct = np.median(quantiles_1pct)

        # Assert within plausible range based on real AMS data (100-50000 m3/s)
        assert 100.0 <= median_q1pct <= 50000.0, (
            f"Median 1% AEP quantile {median_q1pct:.1f} outside plausible range "
            "(100-50000 m3/s)"
        )


class TestFitLP3:
    """Smoke tests for LP3 fitting function."""

    def test_fit_lp3_returns_idata_with_expected_variables(self):
        """Test that fit_lp3 returns InferenceData with mu, sigma, skew."""
        # Generate synthetic LP3 sample (log-space Pearson3)
        np.random.seed(42)
        from scipy.stats import pearson3

        true_mu_log, true_sigma_log, true_skew = 7.0, 0.5, 0.2
        log_sample = pearson3.rvs(true_skew, loc=true_mu_log, scale=true_sigma_log, size=30)
        sample = np.exp(log_sample)
        flows = pd.Series(sample)

        # Fit with reduced draws for test speed
        idata = fit_lp3(flows, draws=500, tune=500)

        # LP3 model uses 'mu', 'sigma', 'skew' as variable names
        assert "mu" in idata.posterior, "Posterior should contain 'mu'"
        assert "sigma" in idata.posterior, "Posterior should contain 'sigma'"
        assert "skew" in idata.posterior, "Posterior should contain 'skew'"

    def test_fit_lp3_1pct_aep_quantile_in_plausible_range(self):
        """Test that 1% AEP quantile is within physically plausible range."""
        np.random.seed(42)
        from scipy.stats import pearson3

        true_mu_log, true_sigma_log, true_skew = 7.0, 0.5, 0.2
        log_sample = pearson3.rvs(true_skew, loc=true_mu_log, scale=true_sigma_log, size=30)
        sample = np.exp(log_sample)
        flows = pd.Series(sample)

        idata = fit_lp3(flows, draws=500, tune=500)

        # Calculate posterior median 1% AEP quantile
        mu_samples = idata.posterior["mu"].values.flatten()
        sigma_samples = idata.posterior["sigma"].values.flatten()
        skew_samples = idata.posterior["skew"].values.flatten()

        quantiles_1pct = [
            get_lp3_quantile(mu, sigma, skew, 1.0)
            for mu, sigma, skew in zip(mu_samples, sigma_samples, skew_samples)
        ]
        median_q1pct = np.median(quantiles_1pct)

        # Assert within plausible range based on real AMS data
        assert 100.0 <= median_q1pct <= 50000.0, (
            f"Median 1% AEP quantile {median_q1pct:.1f} outside plausible range "
            "(100-50000 m3/s)"
        )
