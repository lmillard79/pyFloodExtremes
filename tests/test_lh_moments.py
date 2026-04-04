"""Unit tests for LH-moments and PWM computation engine."""

import numpy as np
import pytest
from scipy.stats import genextreme

from flood_ffa.stats.lh_moments import (
    calculate_sample_pwms,
    pwms_to_lh_moments,
    get_gev_theoretical_pwms,
)
from flood_ffa.gev.fit_lh import fit_gev_lh, get_gev_quantile
from flood_ffa.stats.bootstrap import run_parametric_bootstrap


class TestPWMComputation:
    """Tests for Probability Weighted Moments calculation."""

    def test_pwm_b0_equals_sample_mean(self):
        """Test that b_0 (first PWM) equals the sample mean."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        pwms = calculate_sample_pwms(data, max_k=3)

        # b_0 should equal sample mean
        expected_mean = np.mean(data)
        assert np.isclose(pwms[0], expected_mean, rtol=1e-10), (
            f"PWM b_0 ({pwms[0]}) should equal sample mean ({expected_mean})"
        )

    def test_pwm_known_sample_calculation(self):
        """Test PWM computation against hand-calculated values for small sample."""
        # Small sample where we can verify calculation
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        pwms = calculate_sample_pwms(data, max_k=2)

        # For n=5, sorted x = [1,2,3,4,5]
        # b_0 = mean = 3.0 (already tested above)
        assert np.isclose(pwms[0], 3.0, rtol=1e-10)

        # b_1 formula: (1/n) * sum_{j=2}^n [ (j-1)/(n-1) ] * x_(j)
        # j indexes from 1 to n (1-based), but data is 0-indexed
        # weights: j=2: 1/4, j=3: 2/4, j=4: 3/4, j=5: 4/4
        # weighted sum = (1/4)*2 + (2/4)*3 + (3/4)*4 + (4/4)*5 = 0.5 + 1.5 + 3.0 + 5.0 = 10.0
        # b_1 = 10.0 / 5 = 2.0
        expected_b1 = 2.0
        assert np.isclose(pwms[1], expected_b1, rtol=0.01), (
            f"PWM b_1 ({pwms[1]}) should be close to {expected_b1}"
        )

    def test_pwms_increasing_for_ordered_data(self):
        """Test that PWMs have expected ordering for increasing data."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        pwms = calculate_sample_pwms(data, max_k=4)

        # For increasing data, b_0 > b_1 > b_2 ... (decreasing sequence)
        assert pwms[0] > pwms[1], "b_0 should be greater than b_1 for increasing data"
        assert pwms[1] > pwms[2], "b_1 should be greater than b_2 for increasing data"
        assert pwms[2] > pwms[3], "b_2 should be greater than b_3 for increasing data"


class TestLHMomentFitting:
    """Tests for LH-moment parameter estimation."""

    def test_fit_gev_lh_recovers_known_parameters(self):
        """Test that LH-moment fitting recovers known GEV parameters within tolerance."""
        np.random.seed(42)
        true_mu, true_sigma, true_xi = 500.0, 150.0, 0.05

        # Generate synthetic GEV sample
        sample = genextreme.rvs(c=-true_xi, loc=true_mu, scale=true_sigma, size=50)

        # Fit using LH-moments
        result = fit_gev_lh(sample, shift=0)

        assert result["success"], f"Fit should succeed, got: {result.get('message', 'Unknown error')}"

        # Check recovered parameters within 20% tolerance (LH-moments are approximate)
        fitted_mu = result["mu"]
        fitted_sigma = result["sigma"]
        fitted_xi = result["xi"]

        assert np.isclose(fitted_mu, true_mu, rtol=0.2), (
            f"Fitted mu ({fitted_mu:.1f}) deviates too far from true ({true_mu:.1f})"
        )
        assert np.isclose(fitted_sigma, true_sigma, rtol=0.2), (
            f"Fitted sigma ({fitted_sigma:.1f}) deviates too far from true ({true_sigma:.1f})"
        )
        # Xi is harder to estimate with LH-moments on small samples, use looser tolerance
        assert np.isclose(fitted_xi, true_xi, rtol=1.0, atol=0.15), (
            f"Fitted xi ({fitted_xi:.3f}) deviates too far from true ({true_xi:.3f})"
        )

    def test_pwms_to_lh_moments_produces_reasonable_values(self):
        """Test that PWM to LH-moment conversion produces valid L-moments."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        pwms = calculate_sample_pwms(data, max_k=5)
        lh_moments = pwms_to_lh_moments(pwms, shift=0)

        # L-moments should be: lambda_1 = mean, lambda_2 > 0 (scale), etc.
        assert lh_moments[0] > 0, "L-location (lambda_1) should be positive"
        assert lh_moments[1] > 0, "L-scale (lambda_2) should be positive"


class TestBootstrapCI:
    """Tests for parametric bootstrap confidence intervals."""

    def test_bootstrap_ci_brackets_fitted_quantile(self):
        """Test that bootstrap CI brackets the fitted 1% AEP quantile."""
        np.random.seed(42)
        true_mu, true_sigma, true_xi = 500.0, 150.0, 0.05

        # Generate synthetic sample and fit
        sample = genextreme.rvs(c=-true_xi, loc=true_mu, scale=true_sigma, size=40)
        fit_result = fit_gev_lh(sample, shift=0)

        assert fit_result["success"], "Initial fit should succeed"

        # Calculate fitted 1% AEP quantile
        fitted_q = get_gev_quantile(
            fit_result["mu"], fit_result["sigma"], fit_result["xi"], 1.0
        )

        # Run parametric bootstrap (reduced simulations for test speed)
        aep_grid = np.array([1.0])
        bootstrap_quants = run_parametric_bootstrap(
            fit_func=fit_gev_lh,
            quantile_func=get_gev_quantile,
            params=fit_result,
            n_obs=len(sample),
            aep_grid=aep_grid,
            n_sim=100,  # Reduced for test speed
            dist_type="gev",
        )

        # Remove NaN values (failed fits)
        valid_quants = bootstrap_quants[~np.isnan(bootstrap_quants[:, 0]), 0]

        assert len(valid_quants) > 50, "At least 50 bootstrap samples should succeed"

        # Calculate 90% CI
        ci_lower = np.percentile(valid_quants, 5)
        ci_upper = np.percentile(valid_quants, 95)

        # Fitted quantile should fall within CI (most of the time)
        # Note: This can occasionally fail due to sampling variability,
        # but with fixed seed it should be deterministic
        assert ci_lower <= fitted_q <= ci_upper, (
            f"Fitted quantile ({fitted_q:.1f}) should fall within "
            f"bootstrap CI [{ci_lower:.1f}, {ci_upper:.1f}]"
        )
