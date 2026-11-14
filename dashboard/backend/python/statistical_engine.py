#!/usr/bin/env python3
"""
Scientific Statistical Engine for NASA Space Apps: Earth Systems Trend Detective
Calculates:
- Ordinary Least Squares (OLS) Linear Regression (slope, intercept, r2, p-value, 95% CI)
- Non-parametric Mann-Kendall Rank Trend Test (S, Var(S), Z, Tau, two-tailed p-value with tie handling)
- Theil-Sen Robust Estimator (Sen's Slope, 95% CI)
- Climatological & Seasonal Decomposition
- Multi-region comparison & 255-node Spatial Mapping
"""

import sys
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Path discovery
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = BASE_DIR / "data" / "processed" / "nasa_power_grid_2deg.parquet"
NODES_PATH = BASE_DIR / "data" / "processed" / "gnn_dataset" / "spherical_graph_nodes.csv"

VARIABLE_METADATA = {
    "T2M": {
        "name": "Air Temperature at 2m",
        "units": "°C",
        "description": "Monthly mean near-surface air temperature assimilated from NASA MERRA-2 via NASA POWER.",
        "annual_factor": 12.0
    },
    "PRECTOTCORR": {
        "name": "Precipitation Rate",
        "units": "mm/day",
        "description": "Bias-corrected monthly total precipitation rate from NASA POWER.",
        "annual_factor": 12.0
    },
    "RH2M": {
        "name": "Relative Humidity at 2m",
        "units": "%",
        "description": "Monthly mean surface relative humidity at 2 meters from NASA POWER.",
        "annual_factor": 12.0
    },
    "WS10M": {
        "name": "Wind Speed at 10m",
        "units": "m/s",
        "description": "Monthly mean wind speed at 10 meters above ground from NASA POWER.",
        "annual_factor": 12.0
    }
}

REGION_BOUNDARIES = {
    "NW": {"name": "Northwest India", "code": "NW", "lon_min": 68.0, "lon_max": 82.0, "lat_min": 25.0, "lat_max": 39.0},
    "NE": {"name": "Northeast India", "code": "NE", "lon_min": 82.0, "lon_max": 98.0, "lat_min": 25.0, "lat_max": 39.0},
    "CW": {"name": "Central-West India", "code": "CW", "lon_min": 68.0, "lon_max": 82.0, "lat_min": 15.0, "lat_max": 25.0},
    "CE": {"name": "Central-East India", "code": "CE", "lon_min": 82.0, "lon_max": 98.0, "lat_min": 15.0, "lat_max": 25.0},
    "SW": {"name": "Southwest India", "code": "SW", "lon_min": 68.0, "lon_max": 82.0, "lat_min": 6.0, "lat_max": 15.0},
    "SE": {"name": "Southeast India", "code": "SE", "lon_min": 82.0, "lon_max": 98.0, "lat_min": 6.0, "lat_max": 15.0},
    "ALL": {"name": "All India (National Grid)", "code": "ALL", "lon_min": 68.0, "lon_max": 98.0, "lat_min": 6.0, "lat_max": 39.0}
}

REGION_ALIASES = {
    "NORTH_WEST": "NW",
    "NORTHWEST": "NW",
    "NW": "NW",
    "NORTH_EAST": "NE",
    "NORTHEAST": "NE",
    "NE": "NE",
    "CENTRAL_WEST": "CW",
    "CENTRALWEST": "CW",
    "CW": "CW",
    "CENTRAL_EAST": "CE",
    "CENTRALEAST": "CE",
    "CE": "CE",
    "SOUTH_WEST": "SW",
    "SOUTHWEST": "SW",
    "SW": "SW",
    "SOUTH_EAST": "SE",
    "SOUTHEAST": "SE",
    "SE": "SE",
    "ALL": "ALL",
    "ALL_INDIA": "ALL",
    "INDIA": "ALL"
}


def normalize_region(r):
    if not r:
        return "ALL"
    cleaned = str(r).strip().upper().replace(" ", "_").replace("-", "_")
    return REGION_ALIASES.get(cleaned, "ALL")


def assign_region(lons, lats):
    """Vectorized assignment of custom regions based on validated coordinates."""
    conds = [
        (lons < 82.0) & (lats >= 25.0),
        (lons >= 82.0) & (lats >= 25.0),
        (lons < 82.0) & (lats >= 15.0) & (lats < 25.0),
        (lons >= 82.0) & (lats >= 15.0) & (lats < 25.0),
        (lons < 82.0) & (lats < 15.0),
        (lons >= 82.0) & (lats < 15.0)
    ]
    choices = ['NW', 'NE', 'CW', 'CE', 'SW', 'SE']
    return np.select(conds, choices, default='NW')


def load_dataset():
    """Load and validate the 30,600 row 2-degree monthly grid dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Processed NASA POWER dataset not found at {DATA_PATH}")
    
    df = pd.read_parquet(DATA_PATH)
    
    # Standardize column names
    col_mapping = {}
    if 'time' in df.columns and 'date' not in df.columns:
        col_mapping['time'] = 'date'
    if 'grid_latitude' in df.columns and 'lat' not in df.columns:
        col_mapping['grid_latitude'] = 'lat'
    if 'grid_longitude' in df.columns and 'lon' not in df.columns:
        col_mapping['grid_longitude'] = 'lon'
        
    if col_mapping:
        df = df.rename(columns=col_mapping)
        
    if not np.issubdtype(df['date'].dtype, np.datetime64):
        df['date'] = pd.to_datetime(df['date'])
        
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['date_str'] = df['date'].dt.strftime('%Y-%m')
    
    if 'region' not in df.columns:
        df['region'] = assign_region(df['lon'], df['lat'])
        
    return df


def calculate_mann_kendall(y):
    """
    Computes exact Mann-Kendall S statistic, Var(S) with tie handling,
    tau, standard score Z, and two-tailed p-value.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 4:
        return {"S": 0, "var_s": 0.0, "Z": 0.0, "tau": 0.0, "p_value": 1.0, "is_significant": False, "trend_direction": "no_trend"}
    
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
        "var_s": round(float(var_s), 4),
        "Z": round(float(Z), 4),
        "tau": round(float(tau), 4),
        "p_value": round(float(p_value), 6),
        "is_significant": is_sig,
        "trend_direction": direction
    }


def calculate_sen_slope(x, y, annual_factor=12.0):
    """Computes Sen's robust slope and 95% confidence intervals."""
    res = stats.theilslopes(y, x, alpha=0.95)
    slope = float(res.slope)
    intercept = float(res.intercept)
    lower = float(res.low_slope)
    upper = float(res.high_slope)
    
    return {
        "slope_per_step": round(slope, 6),
        "slope_per_year": round(slope * annual_factor, 6),
        "slope_per_decade": round(slope * annual_factor * 10.0, 6),
        "intercept": round(intercept, 4),
        "ci_lower_per_year": round(lower * annual_factor, 6),
        "ci_upper_per_year": round(upper * annual_factor, 6)
    }


def calculate_ols(x, y, annual_factor=12.0):
    """Computes OLS regression slope, intercept, R2, p-value, SE, and 95% CI."""
    reg = stats.linregress(x, y)
    n = len(x)
    dof = max(1, n - 2)
    t_val = stats.t.ppf(0.975, dof)
    
    slope_per_year = reg.slope * annual_factor
    slope_per_decade = slope_per_year * 10.0
    margin = t_val * reg.stderr * annual_factor
    
    return {
        "slope_per_step": round(float(reg.slope), 6),
        "slope_per_year": round(float(slope_per_year), 6),
        "slope_per_decade": round(float(slope_per_decade), 6),
        "intercept": round(float(reg.intercept), 4),
        "r_squared": round(float(reg.rvalue**2), 4),
        "correlation": round(float(reg.rvalue), 4),
        "p_value": round(float(reg.pvalue), 6),
        "std_err": round(float(reg.stderr), 6),
        "ci_lower_per_year": round(float(slope_per_year - margin), 6),
        "ci_upper_per_year": round(float(slope_per_year + margin), 6)
    }


def generate_interpretation(var_meta, region_info, ols, mk, sen, n_obs):
    """Produces rigorous, human-understandable scientific interpretation."""
    unit = var_meta["units"]
    vname = var_meta["name"]
    rname = region_info["name"]
    alpha = 0.05
    
    is_sig = mk["is_significant"]
    p_val = mk["p_value"]
    rate_yr = sen["slope_per_year"]
    rate_dec = sen["slope_per_decade"]
    sign_str = "+" if rate_yr > 0 else ""
    
    if is_sig:
        if rate_yr > 0:
            trend_str = "statistically significant INCREASING trend"
            verdict = "Clear upward trajectory detected across observations."
        else:
            trend_str = "statistically significant DECREASING trend"
            verdict = "Clear downward trajectory detected across observations."
    else:
        trend_str = "NO statistically significant trend"
        verdict = "Observed fluctuations remain within expected natural climatological variability."
        
    summary = (
        f"Over the investigated 10-year period (N={n_obs} monthly time steps), {vname} in {rname} "
        f"exhibits a {trend_str} (Mann-Kendall p = {p_val:.4f}, α = {alpha}). "
        f"The robust rate of change (Sen's slope) is {sign_str}{rate_yr:.4f} {unit}/year "
        f"({sign_str}{rate_dec:.3f} {unit}/decade). {verdict}"
    )
    
    confidence_assessment = (
        f"Ordinary Least Squares regression yielded R² = {ols['r_squared']:.4f} (p = {ols['p_value']:.4f}) "
        f"with a 95% confidence interval of [{ols['ci_lower_per_year']:.4f}, {ols['ci_upper_per_year']:.4f}] {unit}/year. "
        f"Non-parametric Sen's slope estimated [{sen['ci_lower_per_year']:.4f}, {sen['ci_upper_per_year']:.4f}] {unit}/year."
    )
    
    recommendation = (
        f"Analysis is derived from NASA POWER 2°×2° spatial assimilation (255 nodes). "
        f"Seasonality and localized microclimates may induce short-term oscillations. "
        f"Long-term trend confirmation requires multi-decadal observation series."
    )
    
    return {
        "summary": summary,
        "rate_description": f"{sign_str}{rate_yr:.4f} {unit}/year ({sign_str}{rate_dec:.3f} {unit}/decade)",
        "trend_direction": mk["trend_direction"],
        "is_significant": is_sig,
        "confidence_assessment": confidence_assessment,
        "recommendation": recommendation
    }


def analyze_trend(df, variable="T2M", region="ALL", node_id=None, start_date=None, end_date=None):
    """Primary Trend Detective analysis: OLS, Mann-Kendall, Sen's slope & CI envelope."""
    if variable not in VARIABLE_METADATA:
        raise ValueError(f"Unknown variable {variable}. Valid: {list(VARIABLE_METADATA.keys())}")
        
    var_meta = VARIABLE_METADATA[variable]
    region_code = normalize_region(region)
    region_info = REGION_BOUNDARIES.get(region_code, REGION_BOUNDARIES["ALL"])
    
    sub = df.copy()
    if node_id is not None and str(node_id).strip():
        sub = sub[sub['node_id'].astype(str) == str(node_id).strip()]
    elif region_code != "ALL":
        sub = sub[sub['region'] == region_code]
        
    if start_date:
        sub = sub[sub['date_str'] >= str(start_date)[:7]]
    if end_date:
        sub = sub[sub['date_str'] <= str(end_date)[:7]]
        
    if len(sub) == 0:
        return {"error": "No matching records found for specified query."}
        
    grouped = sub.groupby(['date_str', 'date', 'year', 'month'])[variable].agg(['mean', 'std', 'min', 'max']).reset_index()
    grouped.sort_values('date', inplace=True)
    
    n = len(grouped)
    x = np.arange(n, dtype=float)
    y = grouped['mean'].values
    
    if n < 3:
        return {"error": "Insufficient data points (minimum 3 required for trend calculation)."}
        
    ols = calculate_ols(x, y, var_meta["annual_factor"])
    mk = calculate_mann_kendall(y)
    sen = calculate_sen_slope(x, y, var_meta["annual_factor"])
    
    ols_line = ols["intercept"] + ols["slope_per_step"] * x
    sen_line = sen["intercept"] + sen["slope_per_step"] * x
    
    t_val = stats.t.ppf(0.975, max(1, n - 2))
    s_err = np.sqrt(np.sum((y - ols_line)**2) / max(1, n - 2))
    x_mean = np.mean(x)
    s_xx = np.sum((x - x_mean)**2)
    ci_band = t_val * s_err * np.sqrt(1.0/n + (x - x_mean)**2 / max(1e-9, s_xx))
    
    time_series = []
    for idx, row in grouped.reset_index(drop=True).iterrows():
        time_series.append({
            "date": row['date_str'],
            "timestamp": row['date'].isoformat(),
            "year": int(row['year']),
            "month": int(row['month']),
            "value": round(float(row['mean']), 3),
            "std": round(float(row['std']), 3) if not np.isnan(row['std']) else 0.0,
            "min": round(float(row['min']), 3),
            "max": round(float(row['max']), 3),
            "trend_ols": round(float(ols_line[idx]), 3),
            "trend_sen": round(float(sen_line[idx]), 3),
            "ci_lower": round(float(ols_line[idx] - ci_band[idx]), 3),
            "ci_upper": round(float(ols_line[idx] + ci_band[idx]), 3)
        })
        
    interpretation = generate_interpretation(var_meta, region_info, ols, mk, sen, n)
    
    return {
        "variable": variable,
        "variable_name": var_meta["name"],
        "units": var_meta["units"],
        "region": region_code,
        "region_name": region_info["name"],
        "node_id": node_id,
        "date_range": {
            "start": grouped['date_str'].iloc[0],
            "end": grouped['date_str'].iloc[-1],
            "n_months": n
        },
        "summary_statistics": {
            "mean": round(float(np.mean(y)), 3),
            "median": round(float(np.median(y)), 3),
            "std": round(float(np.std(y)), 3),
            "min": round(float(np.min(y)), 3),
            "max": round(float(np.max(y)), 3),
            "q25": round(float(np.percentile(y, 25)), 3),
            "q75": round(float(np.percentile(y, 75)), 3)
        },
        "ols": ols,
        "mann_kendall": mk,
        "sen_slope": sen,
        "interpretation": interpretation,
        "time_series": time_series
    }


def analyze_seasonal(df, variable="T2M", region="ALL", start_date=None, end_date=None):
    """Calculates climatological monthly averages and 4-season breakdown."""
    if variable not in VARIABLE_METADATA:
        raise ValueError(f"Unknown variable {variable}")
    var_meta = VARIABLE_METADATA[variable]
    region_code = normalize_region(region)
    
    sub = df.copy()
    if region_code != "ALL":
        sub = sub[sub['region'] == region_code]
    if start_date:
        sub = sub[sub['date_str'] >= str(start_date)[:7]]
    if end_date:
        sub = sub[sub['date_str'] <= str(end_date)[:7]]
        
    monthly_agg = sub.groupby('month')[variable].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_agg['month_name'] = monthly_agg['month'].apply(lambda m: month_names[m - 1])
    
    def get_season(m):
        if m in [12, 1, 2]:
            return "Winter (DJF)"
        elif m in [3, 4, 5]:
            return "Pre-Monsoon (MAM)"
        elif m in [6, 7, 8, 9]:
            return "Monsoon (JJAS)"
        else:
            return "Post-Monsoon (ON)"
            
    sub['season'] = sub['month'].apply(get_season)
    seasonal_agg = sub.groupby('season')[variable].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
    yearly_seasonal = sub.groupby(['year', 'season'])[variable].mean().reset_index()
    
    return {
        "variable": variable,
        "variable_name": var_meta["name"],
        "units": var_meta["units"],
        "region": region_code,
        "region_name": REGION_BOUNDARIES.get(region_code, REGION_BOUNDARIES["ALL"])["name"],
        "monthly_climatology": [
            {
                "month": int(r['month']),
                "month_name": r['month_name'],
                "mean": round(float(r['mean']), 3),
                "std": round(float(r['std']), 3),
                "min": round(float(r['min']), 3),
                "max": round(float(r['max']), 3)
            }
            for _, r in monthly_agg.iterrows()
        ],
        "seasonal_summary": [
            {
                "season": r['season'],
                "mean": round(float(r['mean']), 3),
                "std": round(float(r['std']), 3),
                "min": round(float(r['min']), 3),
                "max": round(float(r['max']), 3)
            }
            for _, r in seasonal_agg.iterrows()
        ],
        "yearly_seasonal_trends": [
            {
                "year": int(r['year']),
                "season": r['season'],
                "value": round(float(r[variable]), 3)
            }
            for _, r in yearly_seasonal.iterrows()
        ]
    }


def analyze_compare(df, variable="T2M", start_date=None, end_date=None):
    """Compares all 6 regions side-by-side with slope, significance, and baseline comparison."""
    if variable not in VARIABLE_METADATA:
        raise ValueError(f"Unknown variable {variable}")
    var_meta = VARIABLE_METADATA[variable]
    
    regions = ["NW", "NE", "CW", "CE", "SW", "SE", "ALL"]
    results = []
    
    for r in regions:
        res = analyze_trend(df, variable=variable, region=r, start_date=start_date, end_date=end_date)
        if "error" not in res:
            results.append({
                "region": r,
                "region_name": res["region_name"],
                "mean_value": res["summary_statistics"]["mean"],
                "min_value": res["summary_statistics"]["min"],
                "max_value": res["summary_statistics"]["max"],
                "ols_slope_per_year": res["ols"]["slope_per_year"],
                "ols_slope_per_decade": res["ols"]["slope_per_decade"],
                "sen_slope_per_year": res["sen_slope"]["slope_per_year"],
                "sen_slope_per_decade": res["sen_slope"]["slope_per_decade"],
                "mann_kendall_p": res["mann_kendall"]["p_value"],
                "mann_kendall_tau": res["mann_kendall"]["tau"],
                "is_significant": res["mann_kendall"]["is_significant"],
                "trend_direction": res["mann_kendall"]["trend_direction"],
                "r_squared": res["ols"]["r_squared"]
            })
            
    sorted_by_rate = sorted([r for r in results if r["region"] != "ALL"], key=lambda k: k["sen_slope_per_year"], reverse=True)
    fastest_warming = sorted_by_rate[0]["region_name"] if sorted_by_rate else "N/A"
    
    return {
        "variable": variable,
        "variable_name": var_meta["name"],
        "units": var_meta["units"],
        "fastest_increasing_region": fastest_warming,
        "comparisons": results
    }


def analyze_spatial_values(df, variable="T2M", start_date=None, end_date=None):
    """Computes mean value and trend for all 255 nodes for geospatial Leaflet mapping."""
    if variable not in VARIABLE_METADATA:
        raise ValueError(f"Unknown variable {variable}")
        
    sub = df.copy()
    if start_date:
        sub = sub[sub['date_str'] >= str(start_date)[:7]]
    if end_date:
        sub = sub[sub['date_str'] <= str(end_date)[:7]]
        
    nodes = []
    for node_id, group in sub.groupby('node_id'):
        lat = float(group['lat'].iloc[0])
        lon = float(group['lon'].iloc[0])
        region = str(group['region'].iloc[0])
        
        y = group[variable].values
        n = len(y)
        if n >= 6:
            x = np.arange(n, dtype=float)
            reg = stats.linregress(x, y)
            slope_yr = float(reg.slope * 12.0)
            p_val = float(reg.pvalue)
            is_sig = bool(p_val < 0.05)
        else:
            slope_yr = 0.0
            p_val = 1.0
            is_sig = False
            
        nodes.append({
            "node_id": str(node_id),
            "lat": round(lat, 2),
            "lon": round(lon, 2),
            "region": region,
            "mean_value": round(float(np.mean(y)), 2),
            "std_value": round(float(np.std(y)), 2),
            "min_value": round(float(np.min(y)), 2),
            "max_value": round(float(np.max(y)), 2),
            "slope_per_year": round(slope_yr, 4),
            "p_value": round(p_val, 4),
            "is_significant": is_sig
        })
        
    return {
        "variable": variable,
        "units": VARIABLE_METADATA[variable]["units"],
        "n_nodes": len(nodes),
        "nodes": nodes
    }


def main():
    parser = argparse.ArgumentParser(description="NASA Space Apps Statistical Engine CLI")
    parser.add_argument("--mode", type=str, default="trend", choices=["trend", "seasonal", "compare", "spatial_values", "metadata"])
    parser.add_argument("--variable", type=str, default="T2M", choices=["T2M", "PRECTOTCORR", "RH2M", "WS10M"])
    parser.add_argument("--region", type=str, default="ALL")
    parser.add_argument("--node_id", type=str, default=None)
    parser.add_argument("--start_date", type=str, default="2015-01")
    parser.add_argument("--end_date", type=str, default="2024-12")
    parser.add_argument("--json_input", type=str, default=None, help="JSON encoded arguments string")
    
    args = parser.parse_args()
    
    if args.json_input:
        payload = json.loads(args.json_input)
        mode = payload.get("mode", args.mode)
        variable = payload.get("variable", args.variable)
        region = payload.get("region", args.region)
        node_id = payload.get("node_id", args.node_id)
        start_date = payload.get("start_date", args.start_date)
        end_date = payload.get("end_date", args.end_date)
    else:
        mode = args.mode
        variable = args.variable
        region = args.region
        node_id = args.node_id
        start_date = args.start_date
        end_date = args.end_date
        
    try:
        if mode == "metadata":
            output = {
                "variables": VARIABLE_METADATA,
                "regions": REGION_BOUNDARIES,
                "coverage": {
                    "total_nodes": 255,
                    "resolution": "2.0 degree (~222 km)",
                    "date_start": "2015-01",
                    "date_end": "2024-12",
                    "total_months": 120,
                    "total_records": 30600
                }
            }
        else:
            df = load_dataset()
            if mode == "trend":
                output = analyze_trend(df, variable=variable, region=region, node_id=node_id, start_date=start_date, end_date=end_date)
            elif mode == "seasonal":
                output = analyze_seasonal(df, variable=variable, region=region, start_date=start_date, end_date=end_date)
            elif mode == "compare":
                output = analyze_compare(df, variable=variable, start_date=start_date, end_date=end_date)
            elif mode == "spatial_values":
                output = analyze_spatial_values(df, variable=variable, start_date=start_date, end_date=end_date)
            else:
                output = {"error": f"Unknown mode {mode}"}
                
        print(json.dumps(output))
        sys.exit(0)
    except Exception as e:
        err_out = {"error": str(e), "type": type(e).__name__}
        print(json.dumps(err_out), file=sys.stderr)
        print(json.dumps(err_out))
        sys.exit(1)


if __name__ == "__main__":
    main()
