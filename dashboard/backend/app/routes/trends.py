"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Trends Route: Statistical Rate of Change & Significance Analysis
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..schemas import TrendAnalysisRequest, TrendAnalysisResponse, RegionalComparisonRequest, RegionalComparisonResponse, RegionalComparisonItem
from ..services.data_service import data_service
from ..services.trend_engine import trend_engine
from ..services.geographic_service import geo_service

router = APIRouter(prefix="/api/trends", tags=["trends"])

@router.post("/analyze", response_model=TrendAnalysisResponse)
def analyze_trend(req: TrendAnalysisRequest):
    try:
        var_info = data_service.get_variable_info(req.variable)
        if not var_info:
            raise HTTPException(status_code=400, detail=f"Variable '{req.variable}' is not supported.")

        time_series, meta = data_service.extract_time_series(
            variable=req.variable,
            region=req.region or "All_India",
            node_id=req.node_id,
            start_date=req.start_date or "2015-01-01",
            end_date=req.end_date or "2024-12-01",
            aggregation=req.aggregation or "monthly",
            remove_seasonality=req.remove_seasonality or False
        )

        analysis = trend_engine.analyze(
            time_series=time_series,
            variable_id=var_info["id"],
            unit=var_info["unit"],
            aggregation=req.aggregation or "monthly"
        )

        caveats = [
            "Statistical significance at alpha = 0.05 evaluates the null hypothesis of zero monotonic drift.",
            "Atmospheric observations are conditioned by large-scale planetary circulation; statistical correlation does not establish causation.",
            "Missing values in pilot satellite soundings represent cloudy or QA-filtered soundings, never zero concentration."
        ]

        return TrendAnalysisResponse(
            success=True,
            variable=var_info["id"],
            variable_name=var_info["name"],
            unit=var_info["unit"],
            region=req.region or "All_India",
            node_id=req.node_id,
            start_date=req.start_date or "2015-01-01",
            end_date=req.end_date or "2024-12-01",
            sample_size=meta.get("sample_size", len(time_series)),
            missing_count=meta.get("missing_count", 0),
            time_series=time_series,
            linear_regression=analysis["linear_regression"],
            mann_kendall=analysis["mann_kendall"],
            sens_slope=analysis["sens_slope"],
            trend_classification=analysis["classification"],
            significance_level=0.05,
            is_statistically_significant=analysis["is_significant"],
            plain_language_summary=analysis["summary"],
            scientific_caveats=caveats
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
def compare_regions(req: Dict[str, Any]):
    try:
        var_id = req.get("variable", "T2M")
        start_date = req.get("start_date", "2015-01-01")
        end_date = req.get("end_date", "2024-12-01")
        aggregation = req.get("aggregation", "monthly")

        var_info = data_service.get_variable_info(var_id)
        if not var_info:
            raise HTTPException(status_code=400, detail=f"Variable '{var_id}' not supported.")

        regions = geo_service.get_regions()
        items = []

        for reg in regions:
            rid = reg["id"]
            if rid == "All_India":
                continue

            series, meta = data_service.extract_time_series(
                variable=var_id,
                region=rid,
                start_date=start_date,
                end_date=end_date,
                aggregation=aggregation
            )

            if not series:
                continue

            analysis = trend_engine.analyze(series, var_info["id"], var_info["unit"], aggregation)
            mean_val = float(np.mean([pt["value"] for pt in series])) if series else 0.0

            items.append({
                "region_id": rid,
                "region_name": reg["name"],
                "total_nodes": reg["node_count"],
                "observation_count": len(series),
                "mean_value": round(mean_val, 2),
                "annual_rate_of_change": analysis["linear_regression"]["annualized_rate"],
                "unit": var_info["annual_unit"],
                "trend_direction": analysis["mann_kendall"]["trend_direction"],
                "p_value": analysis["mann_kendall"]["p_value"],
                "is_significant": analysis["is_significant"],
                "sens_slope_annual": analysis["sens_slope"]["annualized_rate"],
                "classification": analysis["classification"]
            })

        interpretation = (
            f"Comparison across India's 6 geographical zones for {var_info['name']} over {start_date} to {end_date}. "
            f"Regional variations demonstrate differences in synoptic exposure, elevation, and climatic regimes."
        )

        return {
            "success": True,
            "variable": var_info["id"],
            "variable_name": var_info["name"],
            "unit": var_info["unit"],
            "start_date": start_date,
            "end_date": end_date,
            "regions": items,
            "interpretation": interpretation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
