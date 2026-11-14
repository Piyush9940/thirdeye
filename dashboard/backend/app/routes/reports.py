"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Reports Route: PDF Investigation Dossier Generator
"""

from fastapi import APIRouter, Response, HTTPException
from typing import Dict, Any
from ..services.report_service import report_service
from ..services.data_service import data_service
from ..services.trend_engine import trend_engine

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.post("/generate")
def generate_report(payload: Dict[str, Any]):
    try:
        # If raw analysis is provided in payload, use it; otherwise compute it
        if "linear_regression" in payload:
            report_data = payload
        else:
            var_id = payload.get("variable", "T2M")
            reg_id = payload.get("region", "All_India")
            start_date = payload.get("start_date", "2015-01-01")
            end_date = payload.get("end_date", "2024-12-01")
            
            var_info = data_service.get_variable_info(var_id)
            if not var_info:
                raise HTTPException(status_code=400, detail=f"Variable '{var_id}' not supported.")

            time_series, meta = data_service.extract_time_series(var_id, reg_id, start_date=start_date, end_date=end_date)
            analysis = trend_engine.analyze(time_series, var_info["id"], var_info["unit"])

            report_data = {
                "variable": var_info["id"],
                "variable_name": var_info["name"],
                "unit": var_info["unit"],
                "region": reg_id,
                "start_date": start_date,
                "end_date": end_date,
                "sample_size": len(time_series),
                "linear_regression": analysis["linear_regression"],
                "mann_kendall": analysis["mann_kendall"],
                "sens_slope": analysis["sens_slope"],
                "trend_classification": analysis["classification"],
                "is_statistically_significant": analysis["is_significant"],
                "plain_language_summary": analysis["summary"]
            }

        pdf_bytes = report_service.generate_trend_pdf(report_data)

        filename = f"Trend_Detective_{report_data.get('variable', 'Analysis')}_{report_data.get('region', 'India')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
