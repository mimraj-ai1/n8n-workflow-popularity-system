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

    # Support custom port via CLI argument (e.g., python run_api.py 8080) or PORT env var
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    elif "PORT" in os.environ and os.environ["PORT"].isdigit():
        port = int(os.environ["PORT"])

    print("\n" + "=" * 60)
    print("  n8n Workflow Popularity System — REST API Server")
    print(f"  Live URL:      http://localhost:{port}")
    print(f"  Swagger docs:  http://localhost:{port}/docs")
    print(f"  Dashboard:     http://localhost:{port}/dashboard")
    print("=" * 60 + "\n")

    try:
        uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=False)
    except OSError as err:
        if "10048" in str(err) or "already in use" in str(err).lower() or "address already in use" in str(err).lower():
            alt_port = port + 1
            print(f"\n[NOTICE] Port {port} is currently busy. Starting automatically on port {alt_port}...")
            print(f"  Swagger docs:  http://localhost:{alt_port}/docs")
            print(f"  Dashboard:     http://localhost:{alt_port}/dashboard\n")
            uvicorn.run("src.api.main:app", host="0.0.0.0", port=alt_port, reload=False)
        else:
            raise
