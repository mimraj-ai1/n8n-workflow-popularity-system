import logging
import time
from typing import Dict, Any
from src.storage.db import WorkflowStorage
from src.collectors.youtube_collector import YouTubeCollector
from src.collectors.forum_collector import ForumCollector
from src.collectors.google_trends_collector import GoogleTrendsCollector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_scheduled_pipeline() -> Dict[str, Any]:
    logger.info("=" * 60)
    logger.info("Starting Scheduled Multi-Platform Collection Job...")
    logger.info("=" * 60)

    start_time = time.time()

    yt_collector = YouTubeCollector()
    forum_collector = ForumCollector()
    google_collector = GoogleTrendsCollector()

    yt_entries = yt_collector.collect()
    forum_entries = forum_collector.collect()
    google_entries = google_collector.collect()

    all_entries = yt_entries + forum_entries + google_entries

    storage = WorkflowStorage()
    saved_count = storage.save_workflows(all_entries)

    duration = round(time.time() - start_time, 2)

    summary = {
        "status": "success",
        "duration_seconds": duration,
        "collected_totals": {
            "youtube": len(yt_entries),
            "forum": len(forum_entries),
            "google": len(google_entries),
            "total": len(all_entries)
        },
        "records_saved": saved_count
    }

    logger.info(f"Pipeline completed in {duration}s. Total workflows saved: {saved_count}")
    logger.info("=" * 60)
    return summary

def start_daemon_scheduler(interval_hours: float = 24.0):
    logger.info(f"Starting continuous scheduler daemon running every {interval_hours} hours...")
    try:
        while True:
            run_scheduled_pipeline()
            logger.info(f"Sleeping for {interval_hours} hours until next scheduled run...")
            time.sleep(interval_hours * 3600)
    except KeyboardInterrupt:
        logger.info("Scheduler daemon stopped by user.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="n8n Workflow Popularity Scheduler")
    parser.add_argument("--daemon", action="store_true", help="Run continuously as a scheduler daemon")
    parser.add_argument("--interval-hours", type=float, default=24.0, help="Interval in hours between runs (default: 24)")
    args = parser.parse_args()

    if args.daemon:
        start_daemon_scheduler(interval_hours=args.interval_hours)
    else:
        run_scheduled_pipeline()
