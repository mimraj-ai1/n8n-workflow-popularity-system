@echo off
title n8n Workflow Popularity System - API Server
echo.
echo ============================================================
echo   n8n Workflow Popularity System - REST API Server
echo ============================================================
echo.
echo Checking dependencies...
python -m pip install -r requirements.txt --quiet
echo.
echo Starting API server...
echo   Swagger docs:  http://localhost:8000/docs
echo   Dashboard:     http://localhost:8000/dashboard
echo ============================================================
echo.
python run_api.py
pause
