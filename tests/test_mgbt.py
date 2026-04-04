"""Smoke tests for Multiple Grubbs-Beck Test (MGBT) low outlier detection."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import genextreme

from flood_ffa.preprocessing.mgbt import detect_low_outliers, MGBTResult


class TestMGBTLowOutlierDetection:
    """Tests for MGBT low outlier detection."""

    def test_detects_obvious_low_outlier(self):
        """Test that an obvious low outlier is flagged.

        Creates a series with 49 values around 50-400 m3/s and one obvious
        outlier at 0.5 m3/s (similar to patterns seen in real AMS data).
        """
        np.random.seed(42)

        # Create typical AMS values (simulating Site 133 pattern)
        base_values = np.random.uniform(50.0, 400.0, size=49)

        # Add one obvious low outlier at 0.5 m3/s
        outlier_value = 0.5
        flows_with_outlier = np.concatenate([[outlier_value], base_values])

        # Create pandas Series with year index (1889-1937, like real data)
        years = range(1889, 1889 + len(flows_with_outlier))
        series = pd.Series(flows_with_outlier, index=years)

        result = detect_low_outliers(series)

        # Assert outlier was detected
        assert result.klow >= 1, (
            f"Expected at least 1 low outlier, got klow={result.klow}"
        )
        assert len(result.outlier_indices) >= 1, (
            "Expected at least one outlier index"
        )

        # The outlier (0.5 m3/s) should be in the detected indices
        # (it will be the lowest value after sorting)
        assert outlier_value in series[result.outlier_indices].values, (
            "The 0.5 m3/s outlier should be detected"
        )

        # Threshold should be above the outlier
        if result.low_outlier_threshold is not None:
            assert result.low_outlier_threshold > outlier_value, (
                f"Threshold ({result.low_outlier_threshold}) should be above "
                f"outlier value ({outlier_value})"
            )

    def test_clean_series_returns_zero_outliers(self):
        """Test that a clean series without outliers returns k_low == 0."""
        np.random.seed(42)

        # Generate clean GEV sample (no artificial outliers)
        true_mu, true_sigma, true_xi = 200.0, 80.0, 0.1
        clean_sample = genextreme.rvs(c=-true_xi, loc=true_mu, scale=true_sigma, size=50)

        # Create pandas Series
        years = range(1970, 1970 + len(clean_sample))
        series = pd.Series(clean_sample, index=years)

        result = detect_low_outliers(series)

        # Assert no outliers detected
        assert result.klow == 0, (
            f"Expected k_low=0 for clean series, got k_low={result.klow}"
        )
        assert len(result.outlier_indices) == 0, (
            f"Expected empty outlier_indices, got {len(result.outlier_indices)} items"
        )
        assert result.low_outlier_threshold is None, (
            "Threshold should be None when no outliers detected"
        )

    def test_returns_correct_dataclass_structure(self):
        """Test that detect_low_outliers returns properly structured MGBTResult."""
        np.random.seed(42)

        # Simple test series
        values = np.array([0.5, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        years = range(2000, 2000 + len(values))
        series = pd.Series(values, index=years)

        result = detect_low_outliers(series)

        # Verify MGBTResult structure
        assert isinstance(result, MGBTResult), "Result should be MGBTResult dataclass"
        assert hasattr(result, "klow"), "Result should have klow attribute"
        assert hasattr(result, "low_outlier_threshold"), "Result should have threshold attribute"
        assert hasattr(result, "outlier_indices"), "Result should have outlier_indices attribute"
        assert hasattr(result, "p_values"), "Result should have p_values attribute"
        assert hasattr(result, "cleaned_flows"), "Result should have cleaned_flows attribute"

        # Verify types
        assert isinstance(result.klow, int), "klow should be an integer"
        assert isinstance(result.outlier_indices, list), "outlier_indices should be a list"
        assert isinstance(result.p_values, np.ndarray), "p_values should be numpy array"
        assert isinstance(result.cleaned_flows, pd.Series), "cleaned_flows should be pandas Series"

    def test_cleaned_flows_excludes_outliers(self):
        """Test that cleaned_flows excludes detected outliers."""
        np.random.seed(42)

        # Series with known outlier
        values = np.array([0.5, 1.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0])
        years = range(2000, 2000 + len(values))
        series = pd.Series(values, index=years)

        result = detect_low_outliers(series)

        if result.klow > 0:
            # Cleaned flows should have fewer elements than original
            assert len(result.cleaned_flows) < len(series), (
                "cleaned_flows should have fewer elements than original series"
            )

            # Outlier indices should not be in cleaned flows
            for idx in result.outlier_indices:
                assert idx not in result.cleaned_flows.index, (
                    f"Outlier index {idx} should not be in cleaned_flows"
                )
