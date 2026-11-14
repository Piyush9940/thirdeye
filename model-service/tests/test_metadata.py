"""Unit tests for the /metadata endpoint."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import get_metadata

def test_metadata_endpoint():
    res = get_metadata()
    
    assert res.model_name == "Original MLP Reference Model"
    assert res.architecture.input_features == 8
    assert res.architecture.hidden_units == 32
    assert res.architecture.dropout == 0.2
    assert res.architecture.hidden_activation == "ReLU"
    
    expected_features = [
        "T2M", "PRECTOTCORR", "RH2M", "WS10M", "latitude", "longitude", "month_sin", "month_cos"
    ]
    assert res.feature_order == expected_features
    assert res.target["unit"] == "ppb"
    assert res.checkpoints_count == 15
    assert res.supported_folds == [1, 2, 3]
    assert res.supported_seeds == [7, 21, 42, 77, 123]
    assert len(res.scientific_limitations) >= 5
    assert len(res.benchmark_comparison) == 4
    
    # Confirm rank 1 is Month-Only Baseline
    assert res.benchmark_comparison[0]["rank"] == 1
    assert "Month-Only" in res.benchmark_comparison[0]["model"]

if __name__ == "__main__":
    test_metadata_endpoint()
    print("Metadata tests PASSED.")
