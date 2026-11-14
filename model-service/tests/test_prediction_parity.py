"""Phase 5 Prediction Parity Verification Suite.

Directly compares outputs of:
1. Original local reference MethanePredictor (models/production_reference/inference/predictor.py)
2. Standalone FastAPI model-service endpoint logic

Reports absolute and relative differences across multiple folds and seeds.
Numerical tolerance threshold: 1e-4 ppb (0.0001 ppb).
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import PredictRequest
from app.main import predict_single
from app.config import settings

# Test cases representing seasonal climate regimes across India
BENCHMARK_TEST_VECTORS = [
    {
        "name": "Northwest Warm Pre-Monsoon",
        "fold": 1,
        "seed": 42,
        "features": [32.5, 0.8, 42.0, 4.2, 28.0, 75.0, 0.866, 0.5]
    },
    {
        "name": "Central India Monsoon Cloud-Filtered",
        "fold": 2,
        "seed": 21,
        "features": [27.0, 8.5, 82.0, 3.8, 21.0, 79.0, -0.866, -0.5]
    },
    {
        "name": "Southern Peninsula Post-Monsoon",
        "fold": 3,
        "seed": 77,
        "features": [26.0, 3.2, 74.0, 2.9, 13.0, 80.0, -0.5, 0.866]
    },
    {
        "name": "Northeast Highland Winter",
        "fold": 1,
        "seed": 123,
        "features": [16.5, 0.2, 55.0, 2.1, 26.0, 92.0, 0.0, 1.0]
    },
    {
        "name": "Western Coastal Post-Monsoon",
        "fold": 2,
        "seed": 7,
        "features": [29.2, 4.5, 78.0, 5.1, 19.0, 73.0, -0.966, 0.259]
    }
]

def run_parity_tests():
    print("=" * 70)
    print("       PREDICTION PARITY AUDIT: ORIGINAL PREDICTOR VS FASTAPI        ")
    print("=" * 70)

    # Import original predictor directly from root production reference
    orig_pkg_dir = Path(settings.MODEL_PACKAGE_DIR).resolve()
    orig_inference_dir = orig_pkg_dir / "inference"
    
    if str(orig_inference_dir) not in sys.path:
        sys.path.insert(0, str(orig_inference_dir))
        
    from predictor import MethanePredictor

    all_passed = True
    max_abs_diff = 0.0
    max_rel_diff = 0.0

    print(f"{'Vector Name':<34} | {'Orig (ppb)':<10} | {'API (ppb)':<10} | {'Abs Diff':<10} | {'Rel Diff':<10} | Result")
    print("-" * 95)

    for case in BENCHMARK_TEST_VECTORS:
        fold = case["fold"]
        seed = case["seed"]
        features = case["features"]
        
        # 1. Evaluate with original local reference MethanePredictor
        orig_predictor = MethanePredictor(
            package_dir=orig_pkg_dir,
            fold=fold,
            seed=seed,
            device="cpu"
        )
        orig_res = orig_predictor.predict(features)
        orig_raw = orig_res["prediction_ppb"]
        orig_val = float(orig_raw[0]) if isinstance(orig_raw, (list, np.ndarray)) else float(orig_raw)

        # 2. Evaluate with FastAPI model-service endpoint logic
        req = PredictRequest(fold=fold, seed=seed, features=features)
        api_res = predict_single(req)
        api_val = float(api_res.prediction_ppb)

        # 3. Calculate differences
        abs_diff = abs(orig_val - api_val)
        rel_diff = abs_diff / abs(orig_val) if orig_val != 0 else 0.0

        if abs_diff > max_abs_diff:
            max_abs_diff = abs_diff
        if rel_diff > max_rel_diff:
            max_rel_diff = rel_diff

        # Tolerance: 0.0001 ppb (1e-4)
        passed = abs_diff <= 0.0001
        if not passed:
            all_passed = False

        status_str = "PASS" if passed else "FAIL"
        print(f"{case['name']:<34} | {orig_val:<10.4f} | {api_val:<10.4f} | {abs_diff:<10.6f} | {rel_diff:<10.2e} | {status_str}")

    print("-" * 95)
    print(f"Max Absolute Difference: {max_abs_diff:.6f} ppb (Tolerance: 0.000100 ppb)")
    print(f"Max Relative Difference: {max_rel_diff:.2e}")
    print("=" * 70)
    
    assert all_passed, f"Parity test failed: Max difference {max_abs_diff} exceeded tolerance 0.0001"
    print("ALL PARITY TESTS PASSED SUCCESSFULLY.")

if __name__ == "__main__":
    run_parity_tests()
