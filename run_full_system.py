"""
run_full_system.py — Runs the full multi-platform data collection pipeline.
Collects from YouTube, n8n Forum, and Google Trends, then saves to SQLite.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scheduler.cron import run_scheduled_pipeline

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  n8n Workflow Popularity System — Full Pipeline Run")
    print("=" * 60 + "\n")

    summary = run_scheduled_pipeline()

    print("\n" + "=" * 60)
    print(f"  Status: {summary['status']}")
    print(f"  Duration: {summary['duration_seconds']}s")
    print(f"  YouTube:  {summary['collected_totals']['youtube']} entries")
    print(f"  Forum:    {summary['collected_totals']['forum']} entries")
    print(f"  Trends:   {summary['collected_totals']['google']} entries")
    print(f"  TOTAL:    {summary['collected_totals']['total']} entries saved")
    print("=" * 60 + "\n")
