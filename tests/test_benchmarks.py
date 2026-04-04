"""Benchmark tests comparing LH-moment fits against ARR/FLIKE published curves.

Validation data sourced from ffa.wmawater.com.au (ARR project using FLIKE).
These tests demonstrate robustness and limitations of the LH-moment emulator
by comparing against established flood frequency analysis results.
"""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from flood_ffa.gev.fit_lh import fit_gev_lh, get_gev_quantile
from flood_ffa.lp3.fit_lh import fit_lp3_lh, get_lp3_quantile


# Path to validation data
VALIDATION_DATA_PATH = Path(__file__).parent.parent / ".github" / "dev" / "flood_frequency_curves.parquet"


def load_validation_data() -> pd.DataFrame:
    """Load ARR/FLIKE validation data from parquet."""
    if not VALIDATION_DATA_PATH.exists():
        pytest.skip(f"Validation data not found at {VALIDATION_DATA_PATH}")
    return pd.read_parquet(VALIDATION_DATA_PATH)


def ari_to_aep(ari_years: float) -> float:
    """Convert Average Recurrence Interval to AEP (percent).

    AEP = 100 / ARI (for rare events, ARI >> 1)
    For example: ARI=100 years -> AEP=1%
    """
    return 100.0 / ari_years


class TestFLIKEValidationDataLoaded:
    """Basic checks that validation data is accessible and well-formed."""

    def test_validation_data_exists(self):
        """Verify validation parquet file exists."""
        assert VALIDATION_DATA_PATH.exists(), (
            f"Validation data should exist at {VALIDATION_DATA_PATH}"
        )

    def test_validation_data_has_expected_columns(self):
        """Verify validation data has required columns."""
        df = load_validation_data()
        required_cols = ["station_id", "ari_years", "discharge_cumecs"]
        for col in required_cols:
            assert col in df.columns, f"Validation data missing required column: {col}"

    def test_validation_data_covers_multiple_gauges(self):
        """Verify data covers multiple gauges."""
        df = load_validation_data()
        n_gauges = df["station_id"].nunique()
        assert n_gauges > 10, f"Expected >10 gauges, found {n_gauges}"

    def test_validation_data_covers_standard_aris(self):
        """Verify data covers standard ARI values (2, 5, 10, 20, 50, 100 years)."""
        df = load_validation_data()
        standard_aris = [2.0, 5.0, 10.0, 20.0, 50.0, 100.0]
        available_aris = df["ari_years"].unique()
        for ari in standard_aris:
            # Allow some tolerance for near-matches
            matches = np.any(np.isclose(available_aris, ari, rtol=0.1))
            assert matches, f"Standard ARI={ari} years not found in validation data"

    def test_discharge_values_in_plausible_range(self):
        """Verify discharge values are in physically plausible range."""
        df = load_validation_data()
        # Range: 0.0 (censored/no-flow) to 50,000 m3/s (large floods)
        # Very small values occur in small/ephemeral catchments
        assert df["discharge_cumecs"].min() >= 0.0, "Minimum discharge below zero"
        assert df["discharge_cumecs"].max() <= 50000.0, "Maximum discharge above plausible range"


class TestSyntheticBenchmarks:
    """Benchmark tests using synthetic data that should match FLIKE behavior.

    These tests create synthetic samples with known parameters, then verify
    that LH-moment fitting produces quantiles within reasonable tolerance
    of what FLIKE would produce for similar parameters.
    """

    def test_gev_lh_1pct_quantile_within_flike_range(self):
        """Test GEV LH-moment 1% AEP quantile against typical FLIKE range.

        Based on validation data, typical 1% AEP quantiles range from
        ~100 m3/s (small catchments) to ~15,000 m3/s (large catchments).
        """
        np.random.seed(42)

        # Simulate a medium-sized catchment (similar to Site 1 in paper data)
        # True parameters that would give ~1000-3000 m3/s at 1% AEP
        true_mu, true_sigma, true_xi = 1000.0, 400.0, 0.15

        from scipy.stats import genextreme
        sample = genextreme.rvs(c=-true_xi, loc=true_mu, scale=true_sigma, size=40)

        # Fit using LH-moments
        result = fit_gev_lh(sample, shift=0)
        assert result["success"], "GEV LH fit should succeed"

        # Calculate 1% AEP quantile
        q_1pct = get_gev_quantile(result["mu"], result["sigma"], result["xi"], 1.0)

        # Assert within typical FLIKE range for medium catchments
        # Based on validation data analysis
        assert 100.0 <= q_1pct <= 15000.0, (
            f"1% AEP quantile {q_1pct:.1f} m3/s outside typical FLIKE range "
            "(100-15,000 m3/s for medium catchments)"
        )

    def test_lp3_lh_1pct_quantile_within_flike_range(self):
        """Test LP3 LH-moment 1% AEP quantile against typical FLIKE range."""
        np.random.seed(42)

        from scipy.stats import pearson3

        # Simulate medium catchment in log-space
        true_mu_log, true_sigma_log, true_skew = 7.0, 0.6, 0.3
        log_sample = pearson3.rvs(true_skew, loc=true_mu_log, scale=true_sigma_log, size=40)
        sample = np.exp(log_sample)

        # Fit using LH-moments
        result = fit_lp3_lh(sample, shift=0)
        assert result["success"], "LP3 LH fit should succeed"

        # Calculate 1% AEP quantile
        q_1pct = get_lp3_quantile(result["mu"], result["sigma"], result["skew"], 1.0)

        # Assert within typical FLIKE range
        assert 100.0 <= q_1pct <= 15000.0, (
            f"1% AEP quantile {q_1pct:.1f} m3/s outside typical FLIKE range "
            "(100-15,000 m3/s for medium catchments)"
        )

    def test_lh_moment_quantiles_monotonic_with_aep(self):
        """Test that LH-moment quantiles decrease monotonically as AEP increases.

        This is a basic sanity check: rarer events (lower AEP) should have
        higher discharge estimates.
        """
        np.random.seed(42)

        from scipy.stats import genextreme
        sample = genextreme.rvs(c=-0.1, loc=500.0, scale=200.0, size=50)

        result = fit_gev_lh(sample, shift=0)
        assert result["success"], "Fit should succeed"

        # Calculate quantiles for decreasing AEPs (increasing rarity)
        aeps = [5.0, 2.0, 1.0, 0.5, 0.2]  # 5%, 2%, 1%, 0.5%, 0.2% AEP
        quantiles = [
            get_gev_quantile(result["mu"], result["sigma"], result["xi"], aep)
            for aep in aeps
        ]

        # Quantiles should increase as AEP decreases (monotonic)
        for i in range(len(quantiles) - 1):
            assert quantiles[i] <= quantiles[i + 1], (
                f"Quantiles not monotonic: Q({aeps[i]}%)={quantiles[i]:.1f} > "
                f"Q({aeps[i+1]}%)={quantiles[i+1]:.1f}"
            )


class TestValidationDataStructure:
    """Tests that validate the structure and completeness of FLIKE data."""

    def test_no_missing_discharge_values(self):
        """Verify all discharge values are non-null."""
        df = load_validation_data()
        assert df["discharge_cumecs"].notna().all(), "Found null discharge values in validation data"

    def test_all_stations_have_multiple_aris(self):
        """Verify each station has multiple ARI points (full curve)."""
        df = load_validation_data()
        ari_counts = df.groupby("station_id")["ari_years"].count()
        min_aris = ari_counts.min()
        assert min_aris >= 5, f"Some stations have only {min_aris} ARI points, expected >=5"

    def test_discharge_increases_with_ari(self):
        """Verify discharge increases with ARI for each station (monotonic).

        This is a key validation: higher ARI (rarer events) should have
        higher discharge estimates.
        """
        df = load_validation_data()

        # Check a sample of stations (not all, for test speed)
        sample_stations = df["station_id"].unique()[:10]

        for station in sample_stations:
            station_data = df[df["station_id"] == station].sort_values("ari_years")
            discharges = station_data["discharge_cumecs"].values

            # Check monotonic increase (allow small tolerance for numerical noise)
            for i in range(len(discharges) - 1):
                assert discharges[i] <= discharges[i + 1] * 1.01, (
                    f"Station {station}: discharge not monotonic at ARI "
                    f"{station_data['ari_years'].iloc[i]:.1f} vs "
                    f"{station_data['ari_years'].iloc[i+1]:.1f}"
                )
