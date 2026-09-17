from typing import Optional, List, Dict, Any
import os
from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.storage.db import WorkflowStorage
from src.scheduler.cron import run_scheduled_pipeline

app = FastAPI(
    title="n8n Workflow Popularity API",
    description="REST API serving popular n8n workflows ranked by evidence across YouTube, Forum, and Google Trends.",
    version="1.0.0"
)

# Serve static files for the dashboard
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

storage = WorkflowStorage()

@app.get("/dashboard")
def read_dashboard():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/")
def read_root():
    return {
        "system": "n8n Workflow Popularity System",
        "status": "online",
        "endpoints": [
            "/workflows",
            "/workflows/youtube",
            "/workflows/forum",
            "/workflows/google",
            "/workflows/top",
            "/workflows/refresh",
            "/workflows/schedule"
        ]
    }

@app.get("/workflows")
def get_workflows(
    platform: Optional[str] = Query(None, description="Filter by platform: YouTube, Forum, Google"),
    country: Optional[str] = Query(None, description="Filter by country: US, IN"),
    search: Optional[str] = Query(None, description="Keyword search in workflow name"),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum popularity score (0-100)"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    results = storage.get_all_workflows(
        platform=platform,
        country=country,
        search=search,
        min_score=min_score,
        limit=limit,
        offset=offset
    )
    return {
        "count": len(results),
        "filters": {"platform": platform, "country": country, "search": search, "min_score": min_score},
        "workflows": results
    }

@app.get("/workflows/youtube")
def get_youtube_workflows(country: Optional[str] = None, limit: int = 50):
    results = storage.get_all_workflows(platform="YouTube", country=country, limit=limit)
    return {"platform": "YouTube", "count": len(results), "workflows": results}

@app.get("/workflows/forum")
def get_forum_workflows(country: Optional[str] = None, limit: int = 50):
    results = storage.get_all_workflows(platform="Forum", country=country, limit=limit)
    return {"platform": "Forum", "count": len(results), "workflows": results}

@app.get("/workflows/google")
def get_google_workflows(country: Optional[str] = None, limit: int = 50):
    results = storage.get_all_workflows(platform="Google", country=country, limit=limit)
    return {"platform": "Google", "count": len(results), "workflows": results}

@app.get("/workflows/top")
def get_top_workflows(limit: int = Query(10, ge=1, le=100), platform: Optional[str] = None):
    results = storage.get_top_workflows(limit=limit, platform=platform)
    return {"top_limit": limit, "platform": platform or "All", "workflows": results}

@app.get("/workflows/schedule")
def get_schedule_info():
    return {
        "scheduled_automation": "Active",
        "supported_cadences": ["Daily (24h)", "Weekly (168h)"],
        "trigger_command": "python -m src.scheduler.cron --daemon --interval-hours 24",
        "manual_trigger_endpoint": "POST /workflows/refresh"
    }

@app.post("/workflows/refresh")
def refresh_data(background_tasks: BackgroundTasks, background: bool = Query(False, description="Run collection asynchronously in background")):
    if background:
        background_tasks.add_task(run_scheduled_pipeline)
        return {
            "message": "Data collection refresh scheduled in background.",
            "status": "processing"
        }

    summary = run_scheduled_pipeline()
    return {
        "message": "Data collection refresh completed successfully.",
        "collected_totals": summary["collected_totals"],
        "records_saved": summary["records_saved"],
        "duration_seconds": summary["duration_seconds"]
    }
