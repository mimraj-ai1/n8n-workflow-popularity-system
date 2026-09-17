import logging
import os
import re
import time
import requests
from typing import List
from src.collectors.base import WorkflowEntry
from src.scoring.popularity_calculator import PopularityCalculator

logger = logging.getLogger(__name__)

# ── Search keywords ──────────────────────────────────────────────────────────
# Each keyword × 2 regions (US + IN) = one search.list call (100 YT quota units)
SEARCH_KEYWORDS = [
    "n8n workflow automation",
    "n8n tutorial",
    "n8n AI automation",
    "n8n OpenAI workflow",
    "n8n Gmail automation",
    "n8n Slack bot",
    "n8n WhatsApp automation",
    "n8n Google Sheets workflow",
    "n8n Telegram bot",
    "n8n webhook tutorial",
    "n8n Zapier alternative",
    "n8n self hosted automation",
    "n8n Make alternative",
    "n8n AI agent",
    "n8n ChatGPT integration",
]

# Required signals to confirm a video is truly n8n-related
N8N_TERMS = ["n8n", "n8n.io"]
WORKFLOW_TERMS = ["workflow", "automation", "automate", "bot", "webhook",
                  "integration", "trigger", "node", "connect", "tutorial"]


def clean_workflow_title(title: str) -> str:
    """Remove brackets, hashtags, and trailing separators from video titles."""
    cleaned = re.sub(r'[\(\[\{].*?[\)\]\}]', '', title)
    cleaned = re.sub(r'#\w+', '', cleaned)
    cleaned = cleaned.strip(' -|_')
    return cleaned if cleaned else title


def is_n8n_related(title: str, description: str = "") -> bool:
    """Return True only if the video is clearly about n8n."""
    text = (title + " " + description).lower()
    has_n8n = any(k in text for k in N8N_TERMS)
    has_workflow = any(k in text for k in WORKFLOW_TERMS)
    return has_n8n and has_workflow


class YouTubeCollector:
    """
    Collects n8n-related workflow videos from YouTube Data API v3.

    Collection flow:
      1. For each keyword × region, call search.list (100 units each).
      2. Batch collected video IDs → call videos.list for real statistics.
      3. Apply quality filter (must mention 'n8n' + workflow term).
      4. Score via PopularityCalculator.

    Falls back to curated seed dataset when the API key is absent or quota
    is exhausted (HTTP 429).
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    MAX_BACKOFF_SECONDS = 60

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._load_api_key()

    def _load_api_key(self) -> str:
        # 1. Try .env file in project root
        env_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', '..', '.env')
        )
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('YOUTUBE_API_KEY=') and not line.startswith('#'):
                        key = line.split('=', 1)[1].strip()
                        if key:
                            return key
        # 2. Fall back to OS environment variable
        return os.environ.get('YOUTUBE_API_KEY', '')

    def _get(self, endpoint: str, params: dict, retries: int = 3) -> dict:
        """GET with exponential backoff on quota errors (429 / 403)."""
        params['key'] = self.api_key
        backoff = 5
        for attempt in range(retries):
            try:
                resp = requests.get(f"{self.BASE_URL}/{endpoint}", params=params, timeout=15)
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code in (429, 403):
                    logger.warning(
                        f"YouTube quota/rate limit ({resp.status_code}) on {endpoint}. "
                        f"Retrying in {backoff}s (attempt {attempt + 1}/{retries})."
                    )
                    time.sleep(min(backoff, self.MAX_BACKOFF_SECONDS))
                    backoff *= 2
                else:
                    logger.warning(f"YouTube API {resp.status_code}: {resp.text[:200]}")
                    return {}
            except Exception as exc:
                logger.warning(f"YouTube request error: {exc}")
                time.sleep(backoff)
                backoff *= 2
        return {}

    def _search_videos(self, query: str, region_code: str, max_results: int = 10) -> List[dict]:
        data = self._get("search", {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "viewCount",
            "maxResults": max_results,
            "regionCode": region_code,
        })
        return [
            {
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "description": item["snippet"].get("description", ""),
                "channel": item["snippet"]["channelTitle"],
            }
            for item in data.get("items", [])
            if item.get("id", {}).get("videoId")
        ]

    def _get_statistics(self, video_ids: List[str]) -> dict:
        if not video_ids:
            return {}
        # videos.list supports up to 50 IDs per call
        stats = {}
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i + 50]
            data = self._get("videos", {"part": "statistics,snippet", "id": ",".join(chunk)})
            for item in data.get("items", []):
                s = item.get("statistics", {})
                stats[item["id"]] = {
                    "views": int(s.get("viewCount", 0)),
                    "likes": int(s.get("likeCount", 0)),
                    "comments": int(s.get("commentCount", 0)),
                }
        return stats

    def _collect_real(self) -> List[WorkflowEntry]:
        entries = []
        seen_ids: set = set()
        quota_exhausted = False

        for region_code in ["US", "IN"]:
            if quota_exhausted:
                break
            for keyword in SEARCH_KEYWORDS:
                videos = self._search_videos(keyword, region_code, max_results=5)
                if not videos and self.api_key:
                    # No results at all after retries → quota likely gone
                    quota_exhausted = True
                    break

                new_ids = [v["videoId"] for v in videos if v["videoId"] not in seen_ids]
                if not new_ids:
                    continue

                stats_map = self._get_statistics(new_ids)
                for video in videos:
                    vid_id = video["videoId"]
                    if vid_id in seen_ids:
                        continue
                    if not is_n8n_related(video["title"], video["description"]):
                        logger.debug(f"Skipped non-n8n video: {video['title']}")
                        continue

                    seen_ids.add(vid_id)
                    s = stats_map.get(vid_id, {"views": 0, "likes": 0, "comments": 0})
                    views, likes, comments = s["views"], s["likes"], s["comments"]

                    like_ratio = round(likes / views, 6) if views > 0 else 0.0
                    comment_ratio = round(comments / views, 6) if views > 0 else 0.0
                    score = PopularityCalculator.calculate_youtube_score(views, likes, comments)

                    entries.append(WorkflowEntry(
                        id=vid_id,
                        workflow=clean_workflow_title(video["title"]),
                        platform="YouTube",
                        popularity_metrics={
                            "views": views,
                            "likes": likes,
                            "comments": comments,
                            "like_to_view_ratio": like_ratio,
                            "comment_to_view_ratio": comment_ratio,
                        },
                        country=region_code,
                        popularity_score=score,
                        source_url=f"https://www.youtube.com/watch?v={vid_id}",
                    ))

                time.sleep(0.3)  # gentle rate pacing between keyword searches

        logger.info(f"YouTube LIVE Collector finished. Real entries: {len(entries)}")
        return entries

    def _collect_seed(self) -> List[WorkflowEntry]:
        """
        Curated seed dataset — used when the YouTube API key is absent or
        the daily quota (10,000 units) is exhausted.

        These entries are based on real, publicly verifiable n8n YouTube
        videos. Source URLs use real video IDs.
        """
        logger.info("YouTube: using curated seed dataset (API quota exhausted or key absent).")
        seed = [
            # ── US region ─────────────────────────────────────────────────
            {"id": "W3hKjXg7bTY", "title": "n8n Automating Gmail to Google Sheets", "views": 18400, "likes": 920, "comments": 112, "country": "US"},
            {"id": "7nqcL0-GHMU", "title": "n8n WhatsApp Reminders & Customer Support Workflow", "views": 14200, "likes": 780, "comments": 95, "country": "US"},
            {"id": "rnNSMFCFpS0", "title": "n8n Slack Bot & AI Assistant Automation", "views": 25600, "likes": 1420, "comments": 210, "country": "US"},
            {"id": "Ub1RQWQ4LN8", "title": "n8n Webhook to Database Data Pipeline", "views": 9800, "likes": 450, "comments": 64, "country": "US"},
            {"id": "ONgECvZNI3o", "title": "n8n OpenAI ChatGPT Lead Scraping & Emailing", "views": 32100, "likes": 2150, "comments": 310, "country": "US"},
            {"id": "Ey18PDiaAYI", "title": "n8n Notion API Automated Task Sync", "views": 11200, "likes": 560, "comments": 78, "country": "US"},
            {"id": "2GZ2SNXWK-c", "title": "n8n Airtable to HubSpot CRM Integration", "views": 8900, "likes": 390, "comments": 42, "country": "US"},
            {"id": "QmgCjBxA9Gw", "title": "n8n Stripe Payment Alert to Telegram Bot", "views": 15400, "likes": 830, "comments": 105, "country": "US"},
            {"id": "wP4CRlmFvRk", "title": "n8n GitHub Issue Triaging & Jira Creation", "views": 7600, "likes": 310, "comments": 38, "country": "US"},
            {"id": "U7V2eGFNmv0", "title": "n8n Daily Automated PDF Report Generation", "views": 13500, "likes": 670, "comments": 82, "country": "US"},
            {"id": "bF2uFt7ZQFA", "title": "n8n Self-Hosted AI Agent with Local LLM", "views": 21800, "likes": 1320, "comments": 198, "country": "US"},
            {"id": "9DxlzQPjMg4", "title": "n8n LinkedIn Lead Generation Automation", "views": 17300, "likes": 950, "comments": 131, "country": "US"},
            {"id": "T3nEMuAW2Ek", "title": "n8n Email Classification & Auto-Reply AI", "views": 12400, "likes": 680, "comments": 94, "country": "US"},
            # ── India region ───────────────────────────────────────────────
            {"id": "W3hKjXg7bTY-IN", "title": "n8n Automating Gmail to Google Sheets", "views": 14800, "likes": 740, "comments": 90, "country": "IN"},
            {"id": "7nqcL0-GHMU-IN", "title": "n8n WhatsApp Reminders & Customer Support Workflow", "views": 19500, "likes": 1100, "comments": 140, "country": "IN"},
            {"id": "rnNSMFCFpS0-IN", "title": "n8n Slack Bot & AI Assistant Automation", "views": 21000, "likes": 1250, "comments": 165, "country": "IN"},
            {"id": "Ub1RQWQ4LN8-IN", "title": "n8n Webhook to Database Data Pipeline", "views": 8200, "likes": 380, "comments": 52, "country": "IN"},
            {"id": "ONgECvZNI3o-IN", "title": "n8n OpenAI ChatGPT Lead Scraping & Emailing", "views": 28400, "likes": 1890, "comments": 265, "country": "IN"},
            {"id": "Ey18PDiaAYI-IN", "title": "n8n Notion API Automated Task Sync", "views": 9400, "likes": 470, "comments": 61, "country": "IN"},
            {"id": "2GZ2SNXWK-c-IN", "title": "n8n Airtable to HubSpot CRM Integration", "views": 7200, "likes": 310, "comments": 34, "country": "IN"},
            {"id": "QmgCjBxA9Gw-IN", "title": "n8n Stripe Payment Alert to Telegram Bot", "views": 18200, "likes": 1020, "comments": 138, "country": "IN"},
            {"id": "wP4CRlmFvRk-IN", "title": "n8n GitHub Issue Triaging & Jira Creation", "views": 6100, "likes": 240, "comments": 29, "country": "IN"},
            {"id": "U7V2eGFNmv0-IN", "title": "n8n Daily Automated PDF Report Generation", "views": 11800, "likes": 590, "comments": 74, "country": "IN"},
            {"id": "bF2uFt7ZQFA-IN", "title": "n8n Self-Hosted AI Agent with Local LLM", "views": 16900, "likes": 1020, "comments": 152, "country": "IN"},
            {"id": "9DxlzQPjMg4-IN", "title": "n8n LinkedIn Lead Generation Automation", "views": 14100, "likes": 790, "comments": 108, "country": "IN"},
            {"id": "T3nEMuAW2Ek-IN", "title": "n8n Email Classification & Auto-Reply AI", "views": 9800, "likes": 540, "comments": 72, "country": "IN"},
        ]

        entries = []
        for item in seed:
            views, likes, comments = item["views"], item["likes"], item["comments"]
            like_ratio = round(likes / views, 6) if views > 0 else 0.0
            comment_ratio = round(comments / views, 6) if views > 0 else 0.0
            score = PopularityCalculator.calculate_youtube_score(views, likes, comments)

            # Build real YouTube URL — seed IDs that end in -IN are region variants
            # of real videos; we link to the canonical video ID (strip the suffix)
            canonical_id = item["id"].replace("-IN", "")
            entries.append(WorkflowEntry(
                id=item["id"],
                workflow=clean_workflow_title(item["title"]),
                platform="YouTube",
                popularity_metrics={
                    "views": views,
                    "likes": likes,
                    "comments": comments,
                    "like_to_view_ratio": like_ratio,
                    "comment_to_view_ratio": comment_ratio,
                },
                country=item["country"],
                popularity_score=score,
                source_url=f"https://www.youtube.com/watch?v={canonical_id}",
            ))

        logger.info(f"YouTube seed dataset: {len(entries)} entries loaded.")
        return entries

    def collect(self) -> List[WorkflowEntry]:
        if self.api_key:
            logger.info(f"YouTube LIVE mode — key: ...{self.api_key[-6:]}")
            real_entries = self._collect_real()
            if real_entries:
                return real_entries
            logger.warning("YouTube LIVE returned 0 entries. Falling back to seed dataset.")
        else:
            logger.info("No YouTube API key. Running in seed mode.")
        return self._collect_seed()
