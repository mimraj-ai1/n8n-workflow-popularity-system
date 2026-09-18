#!/usr/bin/env bash
# ============================================================
#  n8n Workflow Popularity System - Setup & Run (macOS / Linux)
# ============================================================
set -e

echo ""
echo "============================================================"
echo "  n8n Workflow Popularity System — Setup & Run"
echo "============================================================"
echo ""

# Step 1: Check Python
echo "[1/4] Checking Python..."
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "ERROR: Python 3.9+ is required but not found in PATH."
    exit 1
fi
$PYTHON_CMD --version
echo "Python found. OK."
echo ""

# Step 2: Install dependencies
echo "[2/4] Installing dependencies..."
$PYTHON_CMD -m pip install --upgrade pip --quiet
$PYTHON_CMD -m pip install -r requirements.txt --quiet
echo "Dependencies installed. OK."
echo ""

# Step 3: Run test suite
echo "[3/4] Running automated tests..."
$PYTHON_CMD run_tests.py
echo ""

# Step 4: Start API Server
echo "============================================================"
echo "  SETUP COMPLETE! Starting REST API server..."
echo "  API Documentation: http://localhost:8000/docs"
echo "  Web Dashboard:     http://localhost:8000/dashboard"
echo "============================================================"
echo ""
$PYTHON_CMD run_api.py
