#!/usr/bin/env bash
# ============================================================
#  n8n Workflow Popularity System - Start API (macOS / Linux)
# ============================================================
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "ERROR: Python 3.9+ is required but not found in PATH."
    exit 1
fi

echo ""
echo "============================================================"
echo "  Starting n8n Workflow Popularity REST API Server..."
echo "  API Docs:  http://localhost:8000/docs"
echo "  Dashboard: http://localhost:8000/dashboard"
echo "============================================================"
echo ""
$PYTHON_CMD run_api.py
