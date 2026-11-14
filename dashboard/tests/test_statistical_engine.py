"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Unit Tests for Statistical Trend Engine
"""

import sys
import unittest
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.trend_engine import trend_engine
from app.services.data_service import data_service
from app.services.geographic_service import geo_service

class TestStatisticalEngine(unittest.TestCase):

    def test_synthetic_linear_trend(self):
        # Create a known upward slope: y = 2.0 * t + 10.0 + noise
        np.random.seed(42)
        n = 60
        t = np.arange(n)
        noise = np.random.normal(0, 0.5, n)
        y = 2.0 * t + 10.0 + noise

        time_series = [{"date": f"2015-{i+1:02d}-01", "value": float(y[i])} for i in range(n)]
        res = trend_engine.analyze(time_series, "TEST_VAR", "units", aggregation="annual")

        self.assertEqual(res["classification"], "Significant Increasing Trend")
        self.assertTrue(res["is_significant"])
        self.assertAlmostEqual(res["linear_regression"]["slope"], 2.0, delta=0.15)
        self.assertAlmostEqual(res["sens_slope"]["slope"], 2.0, delta=0.15)
        self.assertLess(res["mann_kendall"]["p_value"], 0.001)

    def test_insufficient_data(self):
        # Fewer than MIN_OBSERVATIONS_FOR_TREND (12)
        time_series = [{"date": "2021-01-01", "value": 1.0}, {"date": "2021-02-01", "value": 2.0}]
        res = trend_engine.analyze(time_series, "TEST_VAR", "units")
        self.assertEqual(res["classification"], "Insufficient Data")
        self.assertFalse(res["is_significant"])

    def test_actual_climate_t2m_extraction(self):
        series, meta = data_service.extract_time_series(
            "T2M", region="North_West", start_date="2015-01-01", end_date="2024-12-01"
        )
        self.assertEqual(len(series), 120)
        self.assertEqual(meta["sample_size"], 120)

        res = trend_engine.analyze(series, "T2M", "°C", aggregation="monthly")
        self.assertIn("classification", res)
        self.assertIn("linear_regression", res)
        self.assertIn("mann_kendall", res)
        self.assertIn("sens_slope", res)
        self.assertIsNotNone(res["linear_regression"]["annualized_rate"])
        self.assertIsNotNone(res["mann_kendall"]["p_value"])

    def test_geographic_regions(self):
        regions = geo_service.get_regions()
        self.assertEqual(len(regions), 7) # All India + 6 custom zones
        nw_nodes = geo_service.get_nodes_in_region("North_West")
        self.assertGreater(len(nw_nodes), 0)

if __name__ == "__main__":
    unittest.main()
