"""
run_api.py — Starts the FastAPI REST API server.
Open http://localhost:8000/docs for Swagger documentation.
Open http://localhost:8000/dashboard for the live dashboard.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  n8n Workflow Popularity System — REST API Server")
    print("  Swagger docs:  http://localhost:8000/docs")
    print("  Dashboard:     http://localhost:8000/dashboard")
    print("=" * 60 + "\n")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=False)
