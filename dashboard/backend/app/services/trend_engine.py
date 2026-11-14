"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Statistical Trend Engine: OLS Regression, Mann-Kendall & Sen's Slope
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Any, Tuple, Optional
from ..config import ALPHA_THRESHOLD, MIN_OBSERVATIONS_FOR_TREND

class StatisticalTrendEngine:
    """
    Modular Scientific Service executing rigorous statistical trend detection.
    """

    @staticmethod
    def calculate_linear_regression(
        time_index: np.ndarray,
        values: np.ndarray,
        is_monthly: bool = True
    ) -> Dict[str, Any]:
        """
        Ordinary Least Squares regression with exact two-sided p-value and 95% CI.
        """
        n = len(values)
        if n < 2:
            return {
                "slope": 0.0, "annualized_rate": 0.0, "intercept": 0.0,
                "r_squared": 0.0, "std_err": 0.0, "p_value": 1.0,
                "ci_lower": 0.0, "ci_upper": 0.0
            }

        res = stats.linregress(time_index, values)
        slope = float(res.slope)
        intercept = float(res.intercept)
        r_val = float(res.rvalue)
        p_val = float(res.pvalue)
        std_err = float(res.stderr) if res.stderr is not None else 0.0

        multiplier = 12.0 if is_monthly else 1.0
        annualized_rate = slope * multiplier

        # 95% Confidence Interval using Student's t
        t_crit = stats.t.ppf(1 - ALPHA_THRESHOLD / 2, df=n - 2) if n > 2 else 1.96
        ci_lower = (slope - t_crit * std_err) * multiplier
        ci_upper = (slope + t_crit * std_err) * multiplier

        return {
            "slope": round(slope, 6),
            "annualized_rate": round(annualized_rate, 4),
            "intercept": round(intercept, 4),
            "r_squared": round(r_val ** 2, 4),
            "std_err": round(std_err, 6),
            "p_value": float(p_val),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4)
        }

    @staticmethod
    def calculate_mann_kendall(values: np.ndarray) -> Dict[str, Any]:
        """
        Calculates non-parametric Mann-Kendall trend test statistic S, Z, tau and p-value.
        """
        n = len(values)
        if n < 3:
            return {
                "tau": 0.0, "p_value": 1.0, "s_statistic": 0.0,
                "z_score": 0.0, "is_significant": False, "trend_direction": "no_trend"
            }

        t = np.arange(n)
        tau, p_val = stats.kendalltau(t, values)

        # Direct Mann-Kendall S statistic calculation
        s = 0
        for i in range(n - 1):
            s += np.sum(np.sign(values[i + 1:] - values[i]))

        # Variance calculation with ties
        unique_vals, counts = np.unique(values, return_counts=True)
        tie_term = np.sum(counts * (counts - 1) * (2 * counts + 5))
        var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0

        if var_s > 0:
            if s > 0:
                z = (s - 1) / np.sqrt(var_s)
            elif s < 0:
                z = (s + 1) / np.sqrt(var_s)
            else:
                z = 0.0
        else:
            z = 0.0

        p_value_calc = float(p_val) if not np.isnan(p_val) else 1.0
        is_sig = p_value_calc < ALPHA_THRESHOLD

        if is_sig and s > 0:
            direction = "increasing"
        elif is_sig and s < 0:
            direction = "decreasing"
        elif not is_sig and s > 0:
            direction = "slight_increase"
        elif not is_sig and s < 0:
            direction = "slight_decrease"
        else:
            direction = "no_trend"

        return {
            "tau": round(float(tau), 4) if not np.isnan(tau) else 0.0,
            "p_value": p_value_calc,
            "s_statistic": float(s),
            "z_score": round(float(z), 3),
            "is_significant": is_sig,
            "trend_direction": direction
        }

    @staticmethod
    def calculate_sens_slope(
        time_index: np.ndarray,
        values: np.ndarray,
        is_monthly: bool = True
    ) -> Dict[str, Any]:
        """
        Computes Theil-Sen robust estimator (Sen's slope) and 95% confidence intervals.
        """
        n = len(values)
        if n < 2:
            return {"slope": 0.0, "annualized_rate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

        try:
            res = stats.theilslopes(values, time_index, alpha=0.95)
            slope = float(res.slope)
            low_slope = float(res.low_slope)
            high_slope = float(res.high_slope)
        except Exception:
            # Fallback to pairwise slope median
            pairwise_slopes = []
            for i in range(n - 1):
                for j in range(i + 1, n):
                    dt = time_index[j] - time_index[i]
                    if dt != 0:
                        pairwise_slopes.append((values[j] - values[i]) / dt)
            slope = float(np.median(pairwise_slopes)) if pairwise_slopes else 0.0
            low_slope, high_slope = slope, slope

        multiplier = 12.0 if is_monthly else 1.0
        return {
            "slope": round(slope, 6),
            "annualized_rate": round(slope * multiplier, 4),
            "ci_lower": round(low_slope * multiplier, 4),
            "ci_upper": round(high_slope * multiplier, 4)
        }

    @classmethod
    def analyze(
        cls,
        time_series: List[Dict[str, Any]],
        variable_id: str,
        unit: str,
        aggregation: str = "monthly"
    ) -> Dict[str, Any]:
        """
        Unified Trend Pipeline: Runs OLS, Mann-Kendall, Sen's slope, and classifies trend.
        """
        n = len(time_series)
        is_monthly = (aggregation == "monthly")

        if n < MIN_OBSERVATIONS_FOR_TREND:
            return {
                "classification": "Insufficient Data",
                "is_significant": False,
                "linear_regression": {"slope": 0, "annualized_rate": 0, "intercept": 0, "r_squared": 0, "std_err": 0, "p_value": 1.0, "ci_lower": 0, "ci_upper": 0, "unit": unit},
                "mann_kendall": {"tau": 0, "p_value": 1.0, "s_statistic": 0, "z_score": 0, "is_significant": False, "trend_direction": "no_trend"},
                "sens_slope": {"slope": 0, "annualized_rate": 0, "ci_lower": 0, "ci_upper": 0, "unit": unit},
                "summary": f"Only {n} observations available. A minimum of {MIN_OBSERVATIONS_FOR_TREND} points is required for valid statistical trend analysis."
            }

        time_idx = np.arange(n, dtype=float)
        vals = np.array([pt["value"] for pt in time_series], dtype=float)

        ols = cls.calculate_linear_regression(time_idx, vals, is_monthly)
        ols["unit"] = f"{unit} / year" if is_monthly else unit

        mk = cls.calculate_mann_kendall(vals)

        sen = cls.calculate_sens_slope(time_idx, vals, is_monthly)
        sen["unit"] = f"{unit} / year" if is_monthly else unit

        # Classification decision based on significance threshold alpha = 0.05
        p_val = mk["p_value"]
        slope_rate = ols["annualized_rate"]
        is_sig = (p_val < ALPHA_THRESHOLD)

        if is_sig:
            if slope_rate > 0:
                classification = "Significant Increasing Trend"
            elif slope_rate < 0:
                classification = "Significant Decreasing Trend"
            else:
                classification = "No Clear Trend"
        else:
            if abs(slope_rate) < 0.001:
                classification = "No Clear Trend"
            elif slope_rate > 0:
                classification = "Non-Significant Increasing Trend"
            else:
                classification = "Non-Significant Decreasing Trend"

        # Generate Plain Language Interpretation
        direction_word = "increasing" if slope_rate > 0 else "decreasing"
        sig_word = "statistically significant (p < 0.05)" if is_sig else "not statistically significant (p ≥ 0.05)"
        
        summary = (
            f"Over the analyzed period ({n} observation points), {variable_id} exhibits a {direction_word} pattern "
            f"at an annualized rate of {slope_rate:+.3f} {ols['unit']} (Sen's robust slope: {sen['annualized_rate']:+.3f} {sen['unit']}). "
            f"The Mann-Kendall test confirms this trend is {sig_word} with p = {p_val:.4f} (Kendall's tau: {mk['tau']:+.3f}). "
            f"Linear model explains {ols['r_squared']*100:.1f}% of observed temporal variance (R² = {ols['r_squared']:.3f})."
        )

        return {
            "classification": classification,
            "is_significant": is_sig,
            "linear_regression": ols,
            "mann_kendall": mk,
            "sens_slope": sen,
            "summary": summary
        }

trend_engine = StatisticalTrendEngine()
