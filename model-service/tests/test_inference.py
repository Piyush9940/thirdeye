"""Functional inference tests for single and batch predictions."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.schemas import PredictRequest, BatchPredictRequest
from app.main import predict_single, predict_batch

SAMPLE_FEATURES = {
    "T2M": 26.5,
    "PRECTOTCORR": 4.2,
    "RH2M": 65.0,
    "WS10M": 3.1,
    "latitude": 23.0,
    "longitude": 83.0,
    "month_sin": 0.5,
    "month_cos": 0.866
}

def test_single_predict_dict():
    req = PredictRequest(fold=1, seed=42, features=SAMPLE_FEATURES)
    res = predict_single(req)
    assert isinstance(res.prediction_ppb, float)
    assert 1700.0 < res.prediction_ppb < 2100.0
    assert res.output_unit == "ppb"
    assert res.fold == 1
    assert res.seed == 42
    assert res.status == "experimental_reference"
    assert "Not validated for operational methane forecasting" in res.scientific_warning
    assert "Month-Only baseline" in res.scientific_disclosure

def test_single_predict_list():
    feature_list = [26.5, 4.2, 65.0, 3.1, 23.0, 83.0, 0.5, 0.866]
    req = PredictRequest(fold=2, seed=77, features=feature_list)
    res = predict_single(req)
    assert isinstance(res.prediction_ppb, float)
    assert res.fold == 2
    assert res.seed == 77

def test_predict_month_derivation():
    # Pass calendar month=7 (July) instead of explicit sin/cos
    req = PredictRequest(
        fold=3,
        seed=123,
        features={
            "T2M": 28.0,
            "PRECTOTCORR": 8.5,
            "RH2M": 80.0,
            "WS10M": 4.0,
            "lat": 20.0,
            "lon": 78.0,
            "month": 7
        }
    )
    res = predict_single(req)
    assert isinstance(res.prediction_ppb, float)
    assert res.fold == 3
    assert res.seed == 123

def test_batch_predict():
    req = BatchPredictRequest(
        fold=1,
        seed=42,
        items=[
            SAMPLE_FEATURES,
            [24.0, 1.0, 50.0, 2.5, 25.0, 80.0, 0.0, 1.0],
            [30.0, 10.0, 85.0, 5.0, 15.0, 75.0, -0.5, 0.866]
        ]
    )
    res = predict_batch(req)
    assert res.count == 3
    assert len(res.predictions_ppb) == 3
    for p in res.predictions_ppb:
        assert isinstance(p, float)
        assert 1700.0 < p < 2100.0

if __name__ == "__main__":
    test_single_predict_dict()
    test_single_predict_list()
    test_predict_month_derivation()
    test_batch_predict()
    print("Inference tests PASSED.")
