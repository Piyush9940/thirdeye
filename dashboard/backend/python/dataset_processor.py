#!/usr/bin/env python3
"""
Scientific Dataset Ingestion, Validation & Analysis Engine
for NASA Space Apps: Earth Systems Trend Detective

Features:
- Validates user-uploaded datasets (CSV, TSV, NetCDF via xarray)
- Auto-detects temporal columns, coordinate fields, and environmental variables
- Audits missing values, duplicates, and geographical bounding boxes
- Executes rigorous statistical trend tests (OLS, Mann-Kendall with ties, Theil-Sen median slope)
- Compares custom user datasets against NASA POWER 10-year climatology baselines
"""

import sys
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "nasa_power_grid_2deg.parquet"


def safe_float(val, precision=4):
    if val is None or np.isnan(val) or np.isinf(val):
        return None
    return round(float(val), precision)


def calculate_mann_kendall(y):
    """Computes exact Mann-Kendall test statistic S, Var(S), Z, Tau, and p-value."""
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 4:
        return {
            "S": 0, "var_s": 0.0, "Z": 0.0, "tau": 0.0, "p_value": 1.0,
            "is_significant": False, "trend_direction": "no_trend"
        }

    diffs = np.subtract.outer(y, y)
    signs = np.sign(diffs[np.triu_indices(n, k=1)])
    S = int(np.sum(signs))

    unique_vals, counts = np.unique(y, return_counts=True)
    tie_term = np.sum(counts * (counts - 1) * (2 * counts + 5))
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0

    if var_s <= 0:
        Z = 0.0
    elif S > 0:
        Z = (S - 1.0) / np.sqrt(var_s)
    elif S < 0:
        Z = (S + 1.0) / np.sqrt(var_s)
    else:
        Z = 0.0

    p_value = 2.0 * (1.0 - stats.norm.cdf(abs(Z)))

    tau, _ = stats.kendalltau(np.arange(n), y)
    if np.isnan(tau):
        tau = 0.0

    is_sig = bool(p_value < 0.05)
    if is_sig and S > 0:
        direction = "increasing"
    elif is_sig and S < 0:
        direction = "decreasing"
    else:
        direction = "no_trend"

    return {
        "S": S,
        "var_s": safe_float(var_s),
        "Z": safe_float(Z),
        "tau": safe_float(tau),
        "p_value": safe_float(p_value, 6),
        "is_significant": is_sig,
        "trend_direction": direction
    }


def calculate_sen_slope(x, y, annual_factor=1.0):
    """Computes Theil-Sen robust estimator and 95% confidence bounds."""
    res = stats.theilslopes(y, x, alpha=0.95)
    slope = float(res.slope)
    intercept = float(res.intercept)
    lower = float(res.low_slope)
    upper = float(res.high_slope)

    return {
        "slope_per_step": safe_float(slope, 6),
        "slope_per_year": safe_float(slope * annual_factor, 6),
        "slope_per_decade": safe_float(slope * annual_factor * 10.0, 6),
        "intercept": safe_float(intercept),
        "ci_lower_per_year": safe_float(lower * annual_factor, 6),
        "ci_upper_per_year": safe_float(upper * annual_factor, 6)
    }


def calculate_ols(x, y, annual_factor=1.0):
    """Computes OLS regression slope, intercept, R2, p-value, standard error, and 95% CI."""
    reg = stats.linregress(x, y)
    n = len(x)
    dof = max(1, n - 2)
    t_val = stats.t.ppf(0.975, dof)

    slope_per_year = reg.slope * annual_factor
    slope_per_decade = slope_per_year * 10.0
    margin = t_val * reg.stderr * annual_factor

    return {
        "slope_per_step": safe_float(reg.slope, 6),
        "slope_per_year": safe_float(slope_per_year, 6),
        "slope_per_decade": safe_float(slope_per_decade, 6),
        "intercept": safe_float(reg.intercept),
        "r_squared": safe_float(reg.rvalue**2),
        "correlation": safe_float(reg.rvalue),
        "p_value": safe_float(reg.pvalue, 6),
        "std_err": safe_float(reg.stderr, 6),
        "ci_lower_per_year": safe_float(slope_per_year - margin, 6),
        "ci_upper_per_year": safe_float(slope_per_year + margin, 6)
    }


def load_file_dataframe(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = path.suffix.lower()
    if ext in ['.nc', '.netcdf', '.nc4']:
        try:
            import xarray as xr
            ds = xr.open_dataset(path)
            df = ds.to_dataframe().reset_index()
            return df
        except Exception as e:
            raise RuntimeError(f"Could not parse NetCDF file: {str(e)}")
    
    # Try reading as CSV or TSV
    for sep in [',', '\t', ';', '|']:
        try:
            df = pd.read_csv(path, sep=sep, nrows=50)
            if len(df.columns) > 1:
                # Read full file
                return pd.read_csv(path, sep=sep)
        except Exception:
            continue
            
    # Default fallback
    return pd.read_csv(path)


def validate_dataset(file_path):
    path = Path(file_path)
    size_bytes = path.stat().st_size
    df = load_file_dataframe(file_path)

    total_rows = int(len(df))
    total_cols = int(len(df.columns))
    duplicate_rows = int(df.duplicated().sum())

    total_cells = total_rows * total_cols
    total_nulls = int(df.isnull().sum().sum())
    completeness_pct = safe_float(100.0 * (1.0 - (total_nulls / max(1, total_cells))), 2)

    columns = []
    time_candidates = []
    lat_candidates = []
    lon_candidates = []
    var_candidates = []

    time_keywords = ['date', 'time', 'timestamp', 'year', 'datetime', 'month', 'period']
    lat_keywords = ['lat', 'latitude', 'y', 'lat_deg']
    lon_keywords = ['lon', 'long', 'longitude', 'x', 'lon_deg']

    for col in df.columns:
        col_lower = str(col).lower().strip()
        series = df[col]
        null_count = int(series.isnull().sum())
        null_pct = safe_float(100.0 * null_count / max(1, total_rows), 2)
        
        is_num = pd.api.types.is_numeric_dtype(series)
        is_dt = pd.api.types.is_datetime64_any_dtype(series)
        
        # Check if text looks like datetime
        if not is_dt and not is_num:
            try:
                sample_non_null = series.dropna().iloc[:10]
                if len(sample_non_null) > 0:
                    pd.to_datetime(sample_non_null)
                    is_dt = True
            except Exception:
                pass

        col_info = {
            "name": str(col),
            "dtype": str(series.dtype),
            "is_numeric": bool(is_num),
            "is_datetime": bool(is_dt),
            "null_count": null_count,
            "null_pct": null_pct,
            "sample_values": [None if pd.isna(v) else (v if not isinstance(v, (np.integer, np.floating)) else round(float(v), 4)) for v in series.dropna().iloc[:3].tolist()]
        }

        if is_num:
            valid_vals = series.dropna()
            if len(valid_vals) > 0:
                col_info["stats"] = {
                    "min": safe_float(valid_vals.min()),
                    "max": safe_float(valid_vals.max()),
                    "mean": safe_float(valid_vals.mean()),
                    "std": safe_float(valid_vals.std())
                }

        columns.append(col_info)

        # Keyword matching for field mappings
        if any(tk in col_lower for tk in time_keywords) or is_dt:
            time_candidates.append(str(col))
        if any(lk == col_lower or lk in col_lower for lk in lat_keywords) and is_num:
            lat_candidates.append(str(col))
        if any(lk == col_lower or lk in col_lower for lk in lon_keywords) and is_num:
            lon_candidates.append(str(col))
        if is_num and col not in lat_candidates and col not in lon_candidates:
            if col_lower not in ['id', 'index', 'year', 'month', 'day']:
                var_candidates.append(str(col))

    # Best-guess suggested mapping
    suggested_time = time_candidates[0] if time_candidates else None
    suggested_lat = lat_candidates[0] if lat_candidates else None
    suggested_lon = lon_candidates[0] if lon_candidates else None
    suggested_var = var_candidates[0] if var_candidates else None

    # Temporal range detection
    temporal_range = {
        "has_temporal": False,
        "min_date": None,
        "max_date": None,
        "time_points_count": 0,
        "estimated_frequency": "unknown"
    }
    if suggested_time:
        try:
            parsed_dt = pd.to_datetime(df[suggested_time].dropna()).sort_values()
            if len(parsed_dt) > 0:
                temporal_range["has_temporal"] = True
                temporal_range["min_date"] = parsed_dt.iloc[0].strftime('%Y-%m-%d')
                temporal_range["max_date"] = parsed_dt.iloc[-1].strftime('%Y-%m-%d')
                temporal_range["time_points_count"] = int(parsed_dt.nunique())
                
                # Estimate frequency
                if len(parsed_dt) > 1:
                    median_diff_days = (parsed_dt.diff().dt.total_seconds() / 86400).median()
                    if 25 <= median_diff_days <= 32:
                        temporal_range["estimated_frequency"] = "Monthly"
                    elif 0.8 <= median_diff_days <= 1.2:
                        temporal_range["estimated_frequency"] = "Daily"
                    elif 360 <= median_diff_days <= 370:
                        temporal_range["estimated_frequency"] = "Annual"
                    elif median_diff_days < 0.5:
                        temporal_range["estimated_frequency"] = "Sub-daily / Hourly"
                    else:
                        temporal_range["estimated_frequency"] = f"Irregular (~{round(median_diff_days, 1)} days)"
        except Exception:
            pass

    # Spatial bounds detection
    spatial_bounds = {
        "has_spatial": False,
        "lat_min": None,
        "lat_max": None,
        "lon_min": None,
        "lon_max": None,
        "in_india_bounds": False,
        "point_count": 0
    }
    if suggested_lat and suggested_lon:
        try:
            lats = df[suggested_lat].dropna()
            lons = df[suggested_lon].dropna()
            if len(lats) > 0 and len(lons) > 0:
                spatial_bounds["has_spatial"] = True
                spatial_bounds["lat_min"] = safe_float(lats.min(), 3)
                spatial_bounds["lat_max"] = safe_float(lats.max(), 3)
                spatial_bounds["lon_min"] = safe_float(lons.min(), 3)
                spatial_bounds["lon_max"] = safe_float(lons.max(), 3)
                spatial_bounds["point_count"] = int(min(len(lats), len(lons)))

                # India approximate bounding box: 6°N - 38°N, 68°E - 98°E
                in_india = (lats.min() >= 5.0 and lats.max() <= 40.0 and 
                            lons.min() >= 65.0 and lons.max() <= 100.0)
                spatial_bounds["in_india_bounds"] = bool(in_india)
        except Exception:
            pass

    # Data Quality Assessment
    audit_notes = []
    if completeness_pct >= 98.0:
        quality_status = "EXCELLENT"
        audit_notes.append("High-quality dataset: completeness score >= 98%.")
    elif completeness_pct >= 90.0:
        quality_status = "GOOD"
        audit_notes.append("Good completeness (>= 90%). Minor missing entries can be handled via forward-fill or pairwise deletion.")
    elif completeness_pct >= 75.0:
        quality_status = "ACCEPTABLE"
        audit_notes.append("Moderate missing values. Statistical power may be slightly reduced.")
    else:
        quality_status = "DEFICIENT"
        audit_notes.append("High proportion of missing values (> 25%). Caution required during interpretation.")

    if duplicate_rows > 0:
        audit_notes.append(f"Detected {duplicate_rows} duplicate rows. Deduplication recommended.")
    if spatial_bounds["has_spatial"] and spatial_bounds["in_india_bounds"]:
        audit_notes.append("Spatial coordinates match India subcontinent geographic domain (6°N–38°N, 68°E–98°E).")
    if temporal_range["has_temporal"]:
        audit_notes.append(f"Detected temporal span: {temporal_range['min_date']} to {temporal_range['max_date']} ({temporal_range['estimated_frequency']}).")

    # Preview rows
    preview_df = df.head(25).copy()
    # Replace NaNs with None for valid JSON serialization
    preview_rows = preview_df.where(pd.notnull(preview_df), None).to_dict(orient="records")

    return {
        "success": True,
        "filename": path.name,
        "file_size_bytes": size_bytes,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "completeness_score": completeness_pct,
        "duplicate_rows": duplicate_rows,
        "quality_status": quality_status,
        "audit_notes": audit_notes,
        "columns": columns,
        "candidate_mappings": {
            "time_columns": time_candidates,
            "lat_columns": lat_candidates,
            "lon_columns": lon_candidates,
            "variable_columns": var_candidates
        },
        "suggested_mapping": {
            "time_col": suggested_time,
            "lat_col": suggested_lat,
            "lon_col": suggested_lon,
            "variable_col": suggested_var
        },
        "temporal_range": temporal_range,
        "spatial_bounds": spatial_bounds,
        "preview": preview_rows
    }


def analyze_dataset(file_path, variable, time_col=None, lat_col=None, lon_col=None, unit="units", start_date=None, end_date=None):
    df = load_file_dataframe(file_path)

    if variable not in df.columns:
        raise ValueError(f"Variable '{variable}' not found in dataset. Available columns: {list(df.columns)}")

    # Time column handling
    if not time_col:
        # Search for date/time column
        for col in df.columns:
            if str(col).lower() in ['date', 'time', 'timestamp', 'datetime', 'period']:
                time_col = col
                break

    if time_col and time_col in df.columns:
        df['parsed_date'] = pd.to_datetime(df[time_col], errors='coerce')
        df = df.dropna(subset=['parsed_date'])
        if start_date:
            df = df[df['parsed_date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['parsed_date'] <= pd.to_datetime(end_date)]
        df = df.sort_values('parsed_date')
    else:
        df['parsed_date'] = pd.date_range(start='2015-01-01', periods=len(df), freq='MS')

    # Convert variable to numeric and drop invalid
    df[variable] = pd.to_numeric(df[variable], errors='coerce')
    clean_df = df.dropna(subset=[variable]).copy()

    if len(clean_df) < 3:
        raise ValueError(f"Insufficient valid data points for variable '{variable}' (n = {len(clean_df)}). Minimum required is 3.")

    # Spatial aggregation if multiple points exist per timestamp
    if clean_df['parsed_date'].duplicated().any():
        agg_df = clean_df.groupby('parsed_date').agg(
            mean_val=(variable, 'mean'),
            min_val=(variable, 'min'),
            max_val=(variable, 'max'),
            count_val=(variable, 'count')
        ).reset_index()
        series_dates = agg_df['parsed_date']
        series_y = agg_df['mean_val'].values
    else:
        series_dates = clean_df['parsed_date']
        series_y = clean_df[variable].values

    n_obs = len(series_y)
    x_steps = np.arange(n_obs, dtype=float)

    # Estimate frequency factor (e.g. 12 for monthly, 365 for daily, 1 for annual)
    annual_factor = 1.0
    if n_obs > 1:
        diff_days = (series_dates.iloc[-1] - series_dates.iloc[0]).total_seconds() / (86400 * max(1, n_obs - 1))
        if 25 <= diff_days <= 32:
            annual_factor = 12.0
        elif 0.8 <= diff_days <= 1.2:
            annual_factor = 365.25
        elif 350 <= diff_days <= 370:
            annual_factor = 1.0
        else:
            annual_factor = 365.25 / max(1.0, diff_days)

    # 1. OLS Linear Regression
    ols = calculate_ols(x_steps, series_y, annual_factor=annual_factor)

    # 2. Mann-Kendall Trend Test
    mk = calculate_mann_kendall(series_y)

    # 3. Sen's Slope
    sen = calculate_sen_slope(x_steps, series_y, annual_factor=annual_factor)

    # Fitted values and 95% confidence intervals
    slope_step = ols["slope_per_step"] or 0.0
    intercept = ols["intercept"] or 0.0
    fitted_vals = intercept + slope_step * x_steps

    dof = max(1, n_obs - 2)
    t_crit = stats.t.ppf(0.975, dof)
    residuals = series_y - fitted_vals
    s_err = np.sqrt(np.sum(residuals**2) / dof) if dof > 0 else 0.0
    x_mean = np.mean(x_steps)
    ss_x = np.sum((x_steps - x_mean)**2) if np.sum((x_steps - x_mean)**2) > 0 else 1.0

    se_ci = s_err * np.sqrt(1.0 / n_obs + ((x_steps - x_mean)**2) / ss_x)
    ci_lower = fitted_vals - t_crit * se_ci
    ci_upper = fitted_vals + t_crit * se_ci

    # Sen's fitted line
    sen_slope_step = sen["slope_per_step"] or 0.0
    sen_intercept = sen["intercept"] or 0.0
    sen_fitted = sen_intercept + sen_slope_step * x_steps

    # Data points for time series chart
    time_series = []
    for i in range(n_obs):
        d_str = series_dates.iloc[i].strftime('%Y-%m-%d')
        time_series.append({
            "date": d_str,
            "observed": safe_float(series_y[i]),
            "ols_fitted": safe_float(fitted_vals[i]),
            "sen_fitted": safe_float(sen_fitted[i]),
            "ci_lower": safe_float(ci_lower[i]),
            "ci_upper": safe_float(ci_upper[i])
        })

    # Summary Statistics
    summary_stats = {
        "n_observations": n_obs,
        "mean": safe_float(np.mean(series_y)),
        "std": safe_float(np.std(series_y)),
        "min": safe_float(np.min(series_y)),
        "max": safe_float(np.max(series_y)),
        "start_value": safe_float(series_y[0]),
        "end_value": safe_float(series_y[-1]),
        "net_change": safe_float(series_y[-1] - series_y[0]),
        "pct_change": safe_float(100.0 * (series_y[-1] - series_y[0]) / max(abs(series_y[0]), 1e-6), 2)
    }

    # Scientific Verdict Text
    is_sig = mk["is_significant"]
    rate_yr = sen["slope_per_year"] or 0.0
    rate_dec = sen["slope_per_decade"] or 0.0
    p_val = mk["p_value"]
    sign = "+" if rate_yr > 0 else ""

    if is_sig:
        direction_word = "INCREASING (warming / accumulation)" if rate_yr > 0 else "DECREASING (cooling / depletion)"
        verdict = f"Statistically significant {direction_word} trend detected. Rate: {sign}{rate_yr} {unit}/year ({sign}{rate_dec} {unit}/decade) with Mann-Kendall p = {p_val:.4f} (p < 0.05, R² = {ols['r_squared']})."
    else:
        verdict = f"No statistically significant long-term trend detected at α = 0.05. Observed rate of change ({sign}{rate_yr} {unit}/year, p = {p_val:.4f}) does not meet the statistical threshold to reject the null hypothesis of stationarity."

    return {
        "success": True,
        "variable": variable,
        "unit": unit,
        "time_range": {
            "start": series_dates.iloc[0].strftime('%Y-%m-%d'),
            "end": series_dates.iloc[-1].strftime('%Y-%m-%d'),
            "duration_points": n_obs
        },
        "ols": ols,
        "mann_kendall": mk,
        "theil_sen": sen,
        "summary": summary_stats,
        "verdict": verdict,
        "time_series": time_series
    }


def compare_with_baseline(file_path, variable, baseline_var="T2M", time_col=None):
    """
    Compares uploaded custom series against NASA POWER 10-year monthly climatology
    or corresponding baseline variable.
    """
    # 1. Run analysis on uploaded dataset
    user_res = analyze_dataset(file_path, variable, time_col=time_col)

    # 2. Extract baseline series from NASA POWER parquet if available
    baseline_series = []
    corr_coef = None
    rmse = None
    mae = None
    mean_bias = None

    if DATA_PATH.exists():
        try:
            power_df = pd.read_parquet(DATA_PATH)
            # standardize
            if 'time' in power_df.columns and 'date' not in power_df.columns:
                power_df = power_df.rename(columns={'time': 'date'})
            power_df['date'] = pd.to_datetime(power_df['date'])

            # Target baseline variable: fallback to T2M if baseline_var not in columns
            bvar = baseline_var if baseline_var in power_df.columns else "T2M"
            
            # National mean monthly series
            nat_monthly = power_df.groupby('date')[bvar].mean().reset_index().sort_values('date')

            # Create date alignment map
            user_dates = {item['date'][:7]: item['observed'] for item in user_res['time_series']}
            
            aligned_user = []
            aligned_base = []
            aligned_dates = []

            for _, row in nat_monthly.iterrows():
                ym = row['date'].strftime('%Y-%m')
                if ym in user_dates and user_dates[ym] is not None:
                    u_val = user_dates[ym]
                    b_val = float(row[bvar])
                    aligned_user.append(u_val)
                    aligned_base.append(b_val)
                    aligned_dates.append(ym)

            if len(aligned_user) >= 3:
                u_arr = np.array(aligned_user)
                b_arr = np.array(aligned_base)
                
                r, _ = stats.pearsonr(u_arr, b_arr)
                corr_coef = safe_float(r, 4)
                rmse = safe_float(np.sqrt(np.mean((u_arr - b_arr)**2)), 4)
                mae = safe_float(np.mean(np.abs(u_arr - b_arr)), 4)
                mean_bias = safe_float(np.mean(u_arr - b_arr), 4)

                for i in range(len(aligned_dates)):
                    baseline_series.append({
                        "date": aligned_dates[i],
                        "user_value": safe_float(aligned_user[i]),
                        "baseline_value": safe_float(aligned_base[i]),
                        "difference": safe_float(aligned_user[i] - aligned_base[i])
                    })
        except Exception as e:
            pass

    return {
        "success": True,
        "variable": variable,
        "baseline_variable": baseline_var,
        "user_analysis": {
            "ols": user_res["ols"],
            "mann_kendall": user_res["mann_kendall"],
            "theil_sen": user_res["theil_sen"],
            "summary": user_res["summary"],
            "verdict": user_res["verdict"]
        },
        "comparison": {
            "has_alignment": bool(len(baseline_series) >= 3),
            "aligned_points": len(baseline_series),
            "pearson_correlation": corr_coef,
            "rmse": rmse,
            "mae": mae,
            "mean_bias": mean_bias,
            "comparison_notes": (
                f"Comparison over {len(baseline_series)} overlapping monthly periods against NASA POWER national baseline ({baseline_var}). "
                f"Pearson r = {corr_coef if corr_coef is not None else 'N/A'}, RMSE = {rmse if rmse is not None else 'N/A'}, Mean Bias = {mean_bias if mean_bias is not None else 'N/A'}."
            )
        },
        "aligned_series": baseline_series,
        "user_full_series": user_res["time_series"]
    }


def main():
    parser = argparse.ArgumentParser(description="Scientific Dataset Ingestion & Validation CLI")
    parser.add_argument("--action", required=True, choices=["validate", "analyze", "compare"], help="Processing action")
    parser.add_argument("--file", required=True, help="Path to input dataset file")
    parser.add_argument("--variable", default=None, help="Target environmental variable column name")
    parser.add_argument("--time-col", default=None, help="Date/Timestamp column name")
    parser.add_argument("--lat-col", default=None, help="Latitude column name")
    parser.add_argument("--lon-col", default=None, help="Longitude column name")
    parser.add_argument("--unit", default="units", help="Measurement unit")
    parser.add_argument("--start-date", default=None, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", default=None, help="End date (YYYY-MM-DD)")
    parser.add_argument("--baseline-var", default="T2M", help="Baseline variable for comparison")

    args = parser.parse_args()

    try:
        if args.action == "validate":
            result = validate_dataset(args.file)
        elif args.action == "analyze":
            if not args.variable:
                print(json.dumps({"success": False, "error": "--variable is required for analyze action"}))
                sys.exit(1)
            result = analyze_dataset(
                args.file,
                variable=args.variable,
                time_col=args.time_col,
                lat_col=args.lat_col,
                lon_col=args.lon_col,
                unit=args.unit,
                start_date=args.start_date,
                end_date=args.end_date
            )
        elif args.action == "compare":
            if not args.variable:
                print(json.dumps({"success": False, "error": "--variable is required for compare action"}))
                sys.exit(1)
            result = compare_with_baseline(
                args.file,
                variable=args.variable,
                baseline_var=args.baseline_var,
                time_col=args.time_col
            )
        else:
            result = {"success": False, "error": f"Unknown action: {args.action}"}

        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
