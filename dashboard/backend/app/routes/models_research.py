"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Model Research Route: Secondary ML Lab & Live Inference Bridge
"""

import json
import subprocess
from fastapi import APIRouter, HTTPException
from ..schemas import LiveInferenceRequest, LiveInferenceResponse
from ..config import MODEL_REFERENCE_DIR, PYTHON_VENV_PATH, DASHBOARD_EXPORTS_DIR

router = APIRouter(prefix="/api/models", tags=["models"])

@router.get("/results")
def get_model_results():
    comparisons = [
        {"model": "Month-only Diagnostic", "features": "Month Sine & Cosine", "mae": 49.04, "rmse": 52.68, "r2": -10.49, "bias": -46.49},
        {"model": "Original MLP Reference", "features": "8 Features (Climate + Geo + Calendar)", "mae": 53.79, "rmse": 56.87, "r2": -13.35, "bias": -50.85},
        {"model": "Distance-Weighted GCN", "features": "8 Features + Adjacency Graph", "mae": 58.48, "rmse": 60.76, "r2": -11.49, "bias": -58.01},
        {"model": "Climate-only Ablation", "features": "T2M, Precip, RH, Wind, Lat, Lon", "mae": 59.09, "rmse": 63.26, "r2": -13.09, "bias": -58.66},
        {"model": "Global Training Mean Baseline", "features": "Historical Target Mean", "mae": 62.72, "rmse": 65.07, "r2": -11.90, "bias": -62.43},
        {"model": "Unweighted GCN", "features": "8 Features + Binary Adjacency", "mae": 70.93, "rmse": 75.87, "r2": -23.94, "bias": -64.82}
    ]

    folds = [
        {"fold": 1, "eval_period": "2021-02 (Winter)", "eval_nodes": 67, "mae": 45.60, "rmse": 47.58, "r2": -12.41, "bias": -45.60},
        {"fold": 2, "eval_period": "2021-08 (Monsoon Gap)", "eval_nodes": 11, "mae": 99.93, "rmse": 102.17, "r2": -27.67, "bias": -99.93},
        {"fold": 3, "eval_period": "2023-11 (Post-monsoon)", "eval_nodes": 66, "mae": 15.82, "rmse": 20.87, "r2": 0.043, "bias": -7.01}
    ]

    # Load 15 seed metrics from dashboard_exports if available
    seed_metrics = []
    seed_file = DASHBOARD_EXPORTS_DIR / "fold_seed_metrics.json"
    if seed_file.exists():
        with open(seed_file, "r") as f:
            seed_metrics = json.load(f)

    return {
        "success": True,
        "status": "EXPERIMENTAL REFERENCE MODEL — NOT PRODUCTION APPROVED",
        "scientific_disclaimer": (
            "Most reported R² values are negative, indicating that the model performs worse than a constant mean baseline. "
            "Graph Neural Networks (GCN) did not outperform standard MLP models on this sparse pilot dataset. "
            "The model is not an operational forecasting system."
        ),
        "comparisons": comparisons,
        "fold_summary": folds,
        "seed_metrics": seed_metrics
    }

@router.post("/infer", response_model=LiveInferenceResponse)
def run_live_inference(req: LiveInferenceRequest):
    if len(req.features) != 8:
        raise HTTPException(status_code=400, detail="Expected exactly 8 numerical features: [T2M, PRECTOTCORR, RH2M, WS10M, lat, lon, month_sin, month_cos]")

    # Run inference via Python MethanePredictor on CPU
    try:
        script = f"""
import sys, json
sys.path.insert(0, r"{MODEL_REFERENCE_DIR}\\inference")
from predictor import MethanePredictor
p = MethanePredictor(r"{MODEL_REFERENCE_DIR}", fold={req.fold}, seed={req.seed}, device="cpu")
res = p.predict({req.features})
print(json.dumps(res))
"""
        py_exe = str(PYTHON_VENV_PATH)
        proc = subprocess.run([py_exe, "-c", script], capture_output=True, text=True, timeout=10)
        
        if proc.returncode == 0:
            out = json.loads(proc.stdout.strip())
            pred_val = float(out["prediction_ppb"][0])
            return LiveInferenceResponse(
                success=True,
                model="Original MLP Reference Model",
                fold=req.fold,
                seed=req.seed,
                predicted_ch4_ppb=round(pred_val, 2),
                unit="ppb",
                status="experimental_reference",
                warning="Experimental reference output. Not validated for operational forecasting."
            )
        else:
            raise RuntimeError(proc.stderr)
    except Exception as e:
        # Fallback to verified target mean baseline (1861.16 ppb)
        return LiveInferenceResponse(
            success=True,
            model="Target Mean Fallback Baseline",
            fold=req.fold,
            seed=req.seed,
            predicted_ch4_ppb=1861.16,
            unit="ppb",
            status="experimental_reference",
            warning=f"Predictor bridge note ({str(e)[:100]}); returned ground truth training mean."
        )
