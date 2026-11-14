"""Comprehensive test runner for the model-service test suite."""

import sys
import time
from pathlib import Path

# Add model-service root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_health import test_root_endpoint, test_health_endpoint
from tests.test_metadata import test_metadata_endpoint
from tests.test_validation import (
    test_missing_feature_rejected,
    test_nan_feature_rejected,
    test_inf_feature_rejected,
    test_invalid_fold_rejected,
    test_invalid_seed_rejected,
    test_short_feature_array_rejected,
    test_empty_batch_rejected
)
from tests.test_inference import (
    test_single_predict_dict,
    test_single_predict_list,
    test_predict_month_derivation,
    test_batch_predict
)
from tests.test_prediction_parity import run_parity_tests

def main():
    start_time = time.time()
    print("======================================================================")
    print("       MODEL-SERVICE COMPLETE TEST SUITE & PARITY VERIFICATION        ")
    print("======================================================================\n")
    
    passed_count = 0
    total_count = 0
    
    def run_check(name, func):
        nonlocal passed_count, total_count
        total_count += 1
        try:
            func()
            passed_count += 1
            print(f"[PASS] {name}")
        except Exception as e:
            print(f"[FAIL] {name}: {str(e)}")
            raise e

    print("--- 1. HEALTH & ROOT ENDPOINTS ---")
    run_check("GET / root returns service info", test_root_endpoint)
    run_check("GET /health verifies 15/15 checkpoints & PyTorch CPU", test_health_endpoint)

    print("\n--- 2. METADATA & ARCHITECTURE SPECIFICATION ---")
    run_check("GET /metadata returns 8 features & benchmark disclosures", test_metadata_endpoint)

    print("\n--- 3. INPUT VALIDATION & BOUNDARY DEFENSE ---")
    run_check("Reject missing feature with 422", test_missing_feature_rejected)
    run_check("Reject NaN feature with 422/400", test_nan_feature_rejected)
    run_check("Reject Inf feature with 422/400", test_inf_feature_rejected)
    run_check("Reject invalid fold index (>3) with 422/400", test_invalid_fold_rejected)
    run_check("Reject unapproved seed with 422/400", test_invalid_seed_rejected)
    run_check("Reject short feature array (<8) with 422", test_short_feature_array_rejected)
    run_check("Reject empty batch array with 422", test_empty_batch_rejected)

    print("\n--- 4. INFERENCE EXECUTION & PREPROCESSING PIPELINE ---")
    run_check("POST /predict single sample (dict input)", test_single_predict_dict)
    run_check("POST /predict single sample (flat list input)", test_single_predict_list)
    run_check("POST /predict cyclical month derivation (month=7)", test_predict_month_derivation)
    run_check("POST /predict/batch vectorized inference", test_batch_predict)

    print("\n--- 5. PREDICTION PARITY VERIFICATION ---")
    run_parity_tests()
    passed_count += 1
    total_count += 1

    elapsed = time.time() - start_time
    print("\n======================================================================")
    print(f"  MODEL-SERVICE AUDIT SUMMARY: Passed {passed_count}/{total_count} checks in {elapsed:.2f}s")
    print("======================================================================\n")

if __name__ == "__main__":
    main()
