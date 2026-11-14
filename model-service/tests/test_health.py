"""Unit tests for the /health diagnostic endpoint."""

import sys
from pathlib import Path

# Add model-service root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.main import get_health, root

def test_root_endpoint():
    data = root()
    assert data["status"] == "online"
    assert "health" in data["endpoints"]
    assert "metadata" in data["endpoints"]
    assert "predict" in data["endpoints"]

def test_health_endpoint():
    res = get_health()
    assert res.status in ["healthy", "degraded"]
    assert res.service == "Earth Systems Trend Detective - ML Inference Service"
    assert res.checkpoints_expected == 15
    assert res.checkpoints_found == 15
    assert res.all_checkpoints_loaded is True
    assert res.device == "cpu"
    assert res.pytorch_version != ""
    assert res.timestamp_utc != ""

if __name__ == "__main__":
    test_root_endpoint()
    test_health_endpoint()
    print("Health tests PASSED.")
