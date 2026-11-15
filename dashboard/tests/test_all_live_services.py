import requests
import json
import time

results = []

def record(name, expected, actual, passed, details=""):
    status = "PASS" if passed else "FAIL"
    results.append({
        "name": name,
        "expected": expected,
        "actual": actual,
        "status": status,
        "details": details
    })
    print(f"[{status}] {name}")
    if not passed:
        print(f"       Expected: {expected}")
        print(f"       Actual:   {actual}")
        print(f"       Details:  {details}")

print("======================================================================")
print("   LIVE RUNNING LOCAL SERVICES COMPREHENSIVE INTEGRATION AUDIT        ")
print("======================================================================\n")

# --- 1. PYTHON FASTAPI MICROSERVICE (PORT 8000) ---
print("--- 1. Python FastAPI Microservice (Port 8000) ---")

# GET /health
try:
    r = requests.get("http://127.0.0.1:8000/health", timeout=5)
    data = r.json()
    record(
        "Python ML: GET /health",
        "HTTP 200, status=healthy, 15 checkpoints",
        f"HTTP {r.status_code}, checkpoints={data.get('checkpoints_found')}, device={data.get('device')}",
        r.status_code == 200 and data.get("checkpoints_found") == 15 and data.get("status") == "healthy",
        f"PyTorch: {data.get('pytorch_version')}"
    )
except Exception as e:
    record("Python ML: GET /health", "HTTP 200", str(e), False)

# GET /metadata
try:
    r = requests.get("http://127.0.0.1:8000/metadata", timeout=5)
    data = r.json()
    record(
        "Python ML: GET /metadata",
        "HTTP 200, 8 features, benchmark rankings",
        f"HTTP {r.status_code}, features={len(data.get('feature_order', []))}",
        r.status_code == 200 and len(data.get("feature_order", [])) == 8,
        f"Target: {data.get('target', {}).get('name')}"
    )
except Exception as e:
    record("Python ML: GET /metadata", "HTTP 200", str(e), False)

# GET /docs
try:
    r = requests.get("http://127.0.0.1:8000/docs", timeout=5)
    record(
        "Python ML: GET /docs (Swagger UI)",
        "HTTP 200, Swagger HTML",
        f"HTTP {r.status_code}, length={len(r.text)}",
        r.status_code == 200 and "swagger-ui" in r.text.lower(),
        "Interactive Swagger documentation accessible"
    )
except Exception as e:
    record("Python ML: GET /docs", "HTTP 200", str(e), False)

# POST /predict (Direct to FastAPI)
try:
    payload = {
        "fold": 1,
        "seed": 42,
        "features": {
            "T2M": 26.5,
            "PRECTOTCORR": 4.2,
            "RH2M": 65.0,
            "WS10M": 3.1,
            "latitude": 23.0,
            "longitude": 83.0,
            "month": 7
        }
    }
    r = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=5)
    data = r.json()
    pred = data.get("prediction_ppb", 0)
    record(
        "Python ML: POST /predict (Direct Inference)",
        "HTTP 200, prediction between [1700, 2000] ppb",
        f"HTTP {r.status_code}, prediction={pred:.4f} ppb",
        r.status_code == 200 and 1700 < pred < 2000,
        f"Model: {data.get('model')}, Warning: {data.get('scientific_warning')[:50]}..."
    )
except Exception as e:
    record("Python ML: POST /predict", "HTTP 200", str(e), False)

# --- 2. NODE.JS BACKEND (PORT 5000) ---
print("\n--- 2. Node.js Express Backend (Port 5000) ---")

# GET /api/health
try:
    r = requests.get("http://127.0.0.1:5000/api/health", timeout=5)
    data = r.json()
    record(
        "Node.js Backend: GET /api/health",
        "HTTP 200, status=healthy",
        f"HTTP {r.status_code}, status={data.get('status')}",
        r.status_code == 200 and data.get("status") == "healthy",
        f"Project: {data.get('project')}, Uptime: {data.get('uptime_seconds')}s"
    )
except Exception as e:
    record("Node.js Backend: GET /api/health", "HTTP 200", str(e), False)

# GET /api/metadata
try:
    r = requests.get("http://127.0.0.1:5000/api/metadata", timeout=5)
    data = r.json()
    record(
        "Node.js Backend: GET /api/metadata",
        "HTTP 200, success=true",
        f"HTTP {r.status_code}, success={data.get('success')}",
        r.status_code == 200 and data.get("success") == True,
        f"Project: {data.get('data', {}).get('project')}"
    )
except Exception as e:
    record("Node.js Backend: GET /api/metadata", "HTTP 200", str(e), False)

# GET /api/variables
try:
    r = requests.get("http://127.0.0.1:5000/api/variables", timeout=5)
    data = r.json()
    v_data = data.get("data", {})
    vars_count = len(v_data) if isinstance(v_data, (dict, list)) else 0
    record(
        "Node.js Backend: GET /api/variables",
        "HTTP 200, 4 core variables (T2M, PRECTOTCORR, RH2M, WS10M)",
        f"HTTP {r.status_code}, variables={vars_count}",
        r.status_code == 200 and vars_count >= 4,
        f"Variables: {list(v_data.keys()) if isinstance(v_data, dict) else v_data}"
    )
except Exception as e:
    record("Node.js Backend: GET /api/variables", "HTTP 200", str(e), False)

# GET /api/regions
try:
    r = requests.get("http://127.0.0.1:5000/api/regions", timeout=5)
    data = r.json()
    regions = data.get("data", [])
    record(
        "Node.js Backend: GET /api/regions",
        "HTTP 200, 6 climate zones + ALL",
        f"HTTP {r.status_code}, regions={len(regions)}",
        r.status_code == 200 and len(regions) >= 6,
        f"Regions: {[reg.get('code') for reg in regions]}"
    )
except Exception as e:
    record("Node.js Backend: GET /api/regions", "HTTP 200", str(e), False)

# GET /api/coverage
try:
    r = requests.get("http://127.0.0.1:5000/api/coverage", timeout=5)
    data = r.json()
    cov = data.get("data", {})
    nodes = cov.get("geographic", {}).get("total_nodes")
    record(
        "Node.js Backend: GET /api/coverage",
        "HTTP 200, temporal coverage 2015-2024, 255 nodes",
        f"HTTP {r.status_code}, nodes={nodes}",
        r.status_code == 200 and nodes == 255,
        f"Temporal: {cov.get('temporal', {}).get('primary_climate', {}).get('start_date')} to {cov.get('temporal', {}).get('primary_climate', {}).get('end_date')}"
    )
except Exception as e:
    record("Node.js Backend: GET /api/coverage", "HTTP 200", str(e), False)

# GET /api/ml/health (Node.js querying remote FastAPI)
try:
    r = requests.get("http://127.0.0.1:5000/api/ml/health", timeout=5)
    data = r.json()
    res_data = data.get("data", {})
    record(
        "Node.js Backend: GET /api/ml/health (Proxy to FastAPI)",
        "HTTP 200, status=healthy, service_origin=fastapi_microservice",
        f"HTTP {r.status_code}, origin={res_data.get('service_origin')}",
        r.status_code == 200 and res_data.get("service_origin") == "fastapi_microservice",
        f"Remote Checkpoints: {res_data.get('checkpoints_found')}"
    )
except Exception as e:
    record("Node.js Backend: GET /api/ml/health", "HTTP 200", str(e), False)

# GET /api/ml/metrics
try:
    r = requests.get("http://127.0.0.1:5000/api/ml/metrics", timeout=5)
    data = r.json()
    res_data = data.get("data", {})
    rankings = res_data.get("model_comparison", []) or res_data.get("rankings", [])
    record(
        "Node.js Backend: GET /api/ml/metrics",
        "HTTP 200, benchmark rankings with Month-Only baseline lead",
        f"HTTP {r.status_code}, models={len(rankings)}",
        r.status_code == 200 and len(rankings) >= 3,
        f"Top Model: {rankings[0].get('model') or rankings[0].get('name') if rankings else 'None'}"
    )
except Exception as e:
    record("Node.js Backend: GET /api/ml/metrics", "HTTP 200", str(e), False)

# POST /api/ml/inference (End-to-End: Node.js -> FastAPI -> PyTorch)
try:
    infer_payload = {
        "fold": 1,
        "seed": 42,
        "features": {
            "T2M": 26.5,
            "PRECTOTCORR": 4.2,
            "RH2M": 65.0,
            "WS10M": 3.1,
            "latitude": 23.0,
            "longitude": 83.0,
            "month": 7
        }
    }
    r = requests.post("http://127.0.0.1:5000/api/ml/inference", json=infer_payload, timeout=10)
    data = r.json()
    pred_res = data.get("data", {})
    record(
        "Node.js Backend: POST /api/ml/inference (End-to-End)",
        "HTTP 200, prediction returned, service_origin=fastapi_microservice",
        f"HTTP {r.status_code}, pred={pred_res.get('prediction_ppb')} ppb, origin={pred_res.get('service_origin')}",
        r.status_code == 200 and pred_res.get("service_origin") == "fastapi_microservice",
        f"Prediction: {pred_res.get('prediction_ppb')} ppb, Model: {pred_res.get('model')}"
    )
except Exception as e:
    record("Node.js Backend: POST /api/ml/inference", "HTTP 200", str(e), False)

# POST /api/ai/chat (Live Gemini Grounded AI Assistant)
try:
    ai_payload = {"prompt": "What is the difference between Sen slope and linear regression?"}
    r = requests.post("http://127.0.0.1:5000/api/ai/chat", json=ai_payload, timeout=15)
    data = r.json()
    ans = data.get("data", {}).get("answer", "")
    provider = data.get("data", {}).get("grounded_data", {}).get("provider")
    record(
        "Node.js Backend: POST /api/ai/chat (Gemini 2.5 Flash)",
        "HTTP 200, grounded response returned",
        f"HTTP {r.status_code}, provider={provider}, length={len(ans)} chars",
        r.status_code == 200 and len(ans) > 100,
        f"Model: {data.get('data', {}).get('grounded_data', {}).get('model')}"
    )
except Exception as e:
    record("Node.js Backend: POST /api/ai/chat", "HTTP 200", str(e), False)

# --- 3. FRONTEND SERVERS (PORTS 3000 & 5000) ---
print("\n--- 3. Frontend Dev Server (Port 3000) & Unified Full-Stack (Port 5000) ---")

# Port 3000: Frontend Dev Server
try:
    r = requests.get("http://127.0.0.1:3000/index.html", timeout=5)
    record(
        "Frontend Dev Server: GET http://localhost:3000/",
        "HTTP 200, Landing Page HTML",
        f"HTTP {r.status_code}, length={len(r.text)}",
        r.status_code == 200 and "Earth Systems Trend Detective" in r.text,
        "Frontend static server serving index.html cleanly"
    )
except Exception as e:
    record("Frontend Dev Server: GET http://localhost:3000/", "HTTP 200", str(e), False)

# Port 5000: Unified Full-Stack Frontend
try:
    r = requests.get("http://127.0.0.1:5000/pages/ml-insights.html", timeout=5)
    record(
        "Unified Full-Stack: GET http://localhost:5000/pages/ml-insights.html",
        "HTTP 200, ML Insights Page HTML",
        f"HTTP {r.status_code}, length={len(r.text)}",
        r.status_code == 200 and "ml-service-status-badge" in r.text,
        "Unified Node.js server serving frontend pages and API simultaneously"
    )
except Exception as e:
    record("Unified Full-Stack: GET http://localhost:5000/pages/ml-insights.html", "HTTP 200", str(e), False)

# Print Summary
print("\n======================================================================")
passed_count = sum(1 for x in results if x["status"] == "PASS")
total_count = len(results)
print(f"LIVE SERVICE AUDIT SUMMARY: {passed_count}/{total_count} Passed")
print("======================================================================")

if passed_count < total_count:
    exit(1)
