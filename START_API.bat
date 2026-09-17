@echo off
echo === n8n Workflow Popularity System ===
echo.
echo Step 1: Installing dependencies...
pip install -r requirements.txt

echo.
echo Step 2: Running data collection...
python -m src.scheduler.cron

echo.
echo Step 3: Starting API server on http://localhost:8000
echo   Swagger docs: http://localhost:8000/docs
echo   Dashboard:    http://localhost:8000/dashboard
echo.
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
