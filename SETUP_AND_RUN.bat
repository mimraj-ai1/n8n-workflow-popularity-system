@echo off
:: ============================================================
::  n8n Workflow Popularity System - One-Click Setup & Run
::  For Internship Submission - Works on any Windows machine
:: ============================================================
title n8n Workflow Popularity System - Setup

echo.
echo  ============================================================
echo   n8n Workflow Popularity System
echo   Internship Project Setup
echo  ============================================================
echo.

:: Step 1 - Check Python
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is NOT installed.
    echo  Please install Python 3.9+ from https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version
echo  Python found. OK.
echo.

:: Step 2 - Install dependencies
echo [2/4] Installing required Python packages...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  [ERROR] Failed to install packages.
    echo  Check your internet connection and try again.
    pause
    exit /b 1
)
echo  All packages installed. OK.
echo.

:: Step 3 - Run tests
echo [3/4] Running system tests...
python run_tests.py
echo.

:: Step 4 - Run full pipeline to generate data
echo [4/4] Running data collection pipeline (YouTube + Forum + Google Trends)...
python run_full_system.py
echo.

echo  ============================================================
echo   SETUP COMPLETE! Now starting the REST API server...
echo   Open your browser at: http://localhost:8000
echo   API Documentation at: http://localhost:8000/docs
echo  ============================================================
echo.

:: Start the API server
python run_api.py

pause
