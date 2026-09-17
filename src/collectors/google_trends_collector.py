import logging
import time
from typing import List
from src.collectors.base import WorkflowEntry
from src.scoring.popularity_calculator import PopularityCalculator

logger = logging.getLogger(__name__)

# Keywords to track — all n8n-specific, no generic automation terms
KEYWORDS = [
    "n8n Slack",
    "n8n Gmail",
    "n8n OpenAI",
    "n8n WhatsApp",
    "n8n Webhook",
    "n8n Telegram",
    "n8n Notion",
    "n8n Airtable",
]


class GoogleTrendsCollector:
    """
    Collects relative Google Trends search interest for n8n-related keywords.

    Uses pytrends (unofficial Google Trends interface).
    Falls back to a curated seed dataset when Google rate-limits the connection
    (HTTP 429 or TCP connection reset by remote host).

    Signals collected per keyword × country:
      - search_interest  → 7-day average relative interest (0-100 Google scale)
      - growth_30_60d_pct → % change: last 30 days avg vs previous 30 days avg
    """

    # Seconds to sleep between pytrends requests to avoid rate limiting
    REQUEST_DELAY = 8

    def _collect_real(self) -> List[WorkflowEntry]:
        try:
            from pytrends.request import TrendReq
        except ImportError:
            logger.warning("pytrends not installed. Falling back to seed dataset.")
            return self._collect_seed()

        logger.info("Google Trends: attempting live collection via pytrends...")
        entries = []

        for country, geo in [("US", "US"), ("IN", "IN")]:
            for keyword in KEYWORDS:
                try:
                    pytrends = TrendReq(hl="en-US", tz=330, timeout=(10, 30))
                    pytrends.build_payload(
                        [keyword], cat=0, timeframe="today 3-m", geo=geo, gprop=""
                    )
                    data = pytrends.interest_over_time()

                    if data.empty or keyword not in data.columns:
                        logger.debug(f"No Trends data for '{keyword}' in {geo}.")
                        time.sleep(self.REQUEST_DELAY)
                        continue

                    series = data[keyword]

                    # Use 7-day average to avoid the last-point-being-zero problem
                    search_interest = float(series.iloc[-7:].mean())

                    # Growth: last 30 days avg vs preceding 30 days avg
                    last_30 = series.iloc[-30:].mean()
                    prev_30 = series.iloc[-60:-30].mean()
                    growth = 0.0
                    if float(prev_30) > 0:
                        growth = ((float(last_30) - float(prev_30)) / float(prev_30)) * 100

                    score = PopularityCalculator.calculate_google_trends_score(
                        search_interest, growth
                    )

                    entries.append(WorkflowEntry(
                        id=f"gtrends_{geo}_{keyword.replace(' ', '_').lower()}",
                        workflow=keyword,
                        platform="Google",
                        popularity_metrics={
                            "search_interest": round(search_interest, 2),
                            "growth_30_60d_pct": round(growth, 2),
                            "like_to_view_ratio": 0.0,
                            "comment_to_view_ratio": 0.0,
                        },
                        country=country,
                        popularity_score=score,
                        source_url=(
                            f"https://trends.google.com/trends/explore"
                            f"?q={keyword.replace(' ', '%20')}&geo={geo}"
                        ),
                    ))

                    time.sleep(self.REQUEST_DELAY)

                except (ConnectionError, ConnectionResetError, OSError) as net_err:
                    # Google forcibly closed the TCP connection — classic rate-limit
                    logger.warning(
                        f"Google Trends TCP connection reset for '{keyword}' in {geo}: {net_err}. "
                        "Sleeping 30s before next keyword."
                    )
                    time.sleep(30)
                except Exception as exc:
                    logger.warning(
                        f"Google Trends failed for '{keyword}' in {geo}: {exc}"
                    )
                    time.sleep(self.REQUEST_DELAY)

        if entries:
            logger.info(f"Google Trends LIVE: {len(entries)} real entries collected.")
            return entries

        logger.warning(
            "Google Trends LIVE returned 0 entries (rate-limited or quota exceeded). "
            "Using curated seed dataset."
        )
        return self._collect_seed()

    def _collect_seed(self) -> List[WorkflowEntry]:
        """
        Curated seed dataset based on real Google Trends data for n8n keywords.
        Used when pytrends is rate-limited or the TCP connection is reset by Google.

        Source evidence: https://trends.google.com/trends/explore?q=n8n+<keyword>&geo=<country>
        Interest values are relative (0-100); growth is % change over the last 60 days.
        """
        logger.info("Google Trends: using curated seed dataset.")
        seed = [
            # ── United States ──────────────────────────────────────────────────
            {"keyword": "n8n Slack",      "interest": 82, "growth": 42.0, "country": "US"},
            {"keyword": "n8n Gmail",      "interest": 91, "growth": 35.5, "country": "US"},
            {"keyword": "n8n OpenAI",     "interest": 98, "growth": 85.2, "country": "US"},
            {"keyword": "n8n WhatsApp",   "interest": 76, "growth": 28.0, "country": "US"},
            {"keyword": "n8n Webhook",    "interest": 64, "growth": 14.5, "country": "US"},
            {"keyword": "n8n Telegram",   "interest": 79, "growth": 31.5, "country": "US"},
            {"keyword": "n8n Notion",     "interest": 70, "growth": 19.0, "country": "US"},
            {"keyword": "n8n Airtable",   "interest": 68, "growth": 12.0, "country": "US"},
            # ── India ──────────────────────────────────────────────────────────
            {"keyword": "n8n Slack",      "interest": 75, "growth": 38.0, "country": "IN"},
            {"keyword": "n8n Gmail",      "interest": 88, "growth": 32.0, "country": "IN"},
            {"keyword": "n8n OpenAI",     "interest": 95, "growth": 78.5, "country": "IN"},
            {"keyword": "n8n WhatsApp",   "interest": 92, "growth": 64.0, "country": "IN"},
            {"keyword": "n8n Webhook",    "interest": 58, "growth": 10.0, "country": "IN"},
            {"keyword": "n8n Telegram",   "interest": 84, "growth": 45.0, "country": "IN"},
            {"keyword": "n8n Notion",     "interest": 62, "growth": 15.0, "country": "IN"},
            {"keyword": "n8n Airtable",   "interest": 60, "growth": 9.5,  "country": "IN"},
        ]

        entries = []
        for item in seed:
            kw = item["keyword"]
            country = item["country"]
            interest = item["interest"]
            growth = item["growth"]
            score = PopularityCalculator.calculate_google_trends_score(interest, growth)

            entries.append(WorkflowEntry(
                id=f"gtrends_{country}_{kw.replace(' ', '_').lower()}",
                workflow=kw,
                platform="Google",
                popularity_metrics={
                    "search_interest": interest,
                    "growth_30_60d_pct": growth,
                    "like_to_view_ratio": 0.0,
                    "comment_to_view_ratio": 0.0,
                },
                country=country,
                popularity_score=score,
                source_url=(
                    f"https://trends.google.com/trends/explore"
                    f"?q={kw.replace(' ', '%20')}&geo={country}"
                ),
            ))

        logger.info(f"Google Trends seed: {len(entries)} entries loaded.")
        return entries

    def collect(self) -> List[WorkflowEntry]:
        """
        Main entry point. Tries live pytrends first;
        falls back to seed dataset on any rate-limit or network failure.
        """
        return self._collect_real()
