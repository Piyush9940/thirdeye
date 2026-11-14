"""
NASA Space Apps Challenge 2026 - Earth Systems Trend Detective
Backend Runner Script
"""

import uvicorn
from app.config import HOST, PORT

if __name__ == "__main__":
    print(f"Starting Earth Systems Trend Detective Scientific API on http://{HOST}:{PORT}...")
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
