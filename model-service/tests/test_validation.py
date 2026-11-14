"""Validation test suite ensuring NaN, Inf, missing, and out-of-range inputs are rejected."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import ValidationError
from app.schemas import PredictRequest, BatchPredictRequest, FeatureDict

VALID_SAMPLE = {
    "fold": 1,
    "seed": 42,
    "features": {
        "T2M": 26.5,
        "PRECTOTCORR": 4.2,
        "RH2M": 65.0,
        "WS10M": 3.1,
        "latitude": 23.0,
        "longitude": 83.0,
        "month_sin": 0.5,
        "month_cos": 0.866
    }
}

def test_missing_feature_rejected():
    payload = {
        "fold": 1,
        "seed": 42,
        "features": {
            "T2M": 26.5,
            # PRECTOTCORR missing
            "RH2M": 65.0,
            "WS10M": 3.1,
            "latitude": 23.0,
            "longitude": 83.0
        }
    }
    caught = False
    try:
        PredictRequest(**payload)
    except ValidationError:
        caught = True
    assert caught, "Expected ValidationError for missing feature"

def test_nan_feature_rejected():
    payload = dict(VALID_SAMPLE)
    payload["features"] = dict(VALID_SAMPLE["features"])
    payload["features"]["T2M"] = float("nan")
    
    caught = False
    try:
        PredictRequest(**payload)
    except ValidationError:
        caught = True
    assert caught, "Expected ValidationError for NaN feature"

def test_inf_feature_rejected():
    payload = dict(VALID_SAMPLE)
    payload["features"] = dict(VALID_SAMPLE["features"])
    payload["features"]["WS10M"] = float("inf")
    
    caught = False
    try:
        PredictRequest(**payload)
    except ValidationError:
        caught = True
    assert caught, "Expected ValidationError for Inf feature"

def test_invalid_fold_rejected():
    payload = dict(VALID_SAMPLE)
    payload["fold"] = 4  # Valid folds: 1, 2, 3
    
    caught = False
    try:
        PredictRequest(**payload)
    except ValidationError:
        caught = True
    assert caught, "Expected ValidationError for invalid fold"

def test_invalid_seed_rejected():
    payload = dict(VALID_SAMPLE)
    payload["seed"] = 99  # Valid seeds: 7, 21, 42, 77, 123
    
    caught = False
    try:
        PredictRequest(**payload)
    except ValidationError:
        caught = True
    assert caught, "Expected ValidationError for invalid seed"

def test_short_feature_array_rejected():
    payload = {
        "fold": 1,
        "seed": 42,
        "features": [25.0, 3.0, 60.0]  # Only 3 elements instead of 8
    }
    caught = False
    try:
        PredictRequest(**payload)
    except ValidationError:
        caught = True
    assert caught, "Expected ValidationError for short feature list"

def test_empty_batch_rejected():
    payload = {
        "fold": 1,
        "seed": 42,
        "items": []
    }
    caught = False
    try:
        BatchPredictRequest(**payload)
    except ValidationError:
        caught = True
    assert caught, "Expected ValidationError for empty batch"

if __name__ == "__main__":
    test_missing_feature_rejected()
    test_nan_feature_rejected()
    test_inf_feature_rejected()
    test_invalid_fold_rejected()
    test_invalid_seed_rejected()
    test_short_feature_array_rejected()
    test_empty_batch_rejected()
    print("Validation tests PASSED.")
