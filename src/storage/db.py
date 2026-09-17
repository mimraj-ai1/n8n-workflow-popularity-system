import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.collectors.base import WorkflowEntry

logger = logging.getLogger(__name__)

class WorkflowStorage:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_dir = Path(__file__).parent.parent.parent / "data"
            db_dir.mkdir(exist_ok=True)
            db_path = str(db_dir / "workflows.db")

        self.db_path = db_path
        self._mem_conn = None
        if self.db_path == ":memory:":
            self._mem_conn = sqlite3.connect(":memory:")

        self._init_db()

    def _get_connection(self):
        if self._mem_conn:
            return self._mem_conn
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                workflow TEXT NOT NULL,
                platform TEXT NOT NULL,
                popularity_score REAL NOT NULL,
                country TEXT NOT NULL,
                metrics_json TEXT NOT NULL,
                source_url TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform ON workflows(platform)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_country ON workflows(country)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_score ON workflows(popularity_score DESC)")
        conn.commit()
        if not self._mem_conn:
            conn.close()

    def save_workflows(self, entries: List[WorkflowEntry]) -> int:
        saved_count = 0
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for entry in entries:
                d = entry.to_dict()
                entry_id = entry.id or f"{entry.platform.lower()}_{hash(entry.workflow)}_{entry.country}"
                metrics_json = json.dumps(d["popularity_metrics"])

                cursor.execute("""
                    INSERT INTO workflows (id, workflow, platform, popularity_score, country, metrics_json, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        workflow = excluded.workflow,
                        popularity_score = excluded.popularity_score,
                        metrics_json = excluded.metrics_json,
                        source_url = excluded.source_url,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    entry_id,
                    d["workflow"],
                    d["platform"],
                    d["popularity_score"],
                    d["country"],
                    metrics_json,
                    d.get("source_url")
                ))
                saved_count += 1
            conn.commit()
        finally:
            if not self._mem_conn:
                conn.close()

        logger.info(f"Saved/Updated {saved_count} workflow entries in database.")
        return saved_count

    def get_all_workflows(
        self,
        platform: Optional[str] = None,
        country: Optional[str] = None,
        search: Optional[str] = None,
        min_score: float = 0.0,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = "SELECT id, workflow, platform, popularity_score, country, metrics_json, source_url FROM workflows WHERE popularity_score >= ?"
        params: List[Any] = [min_score]

        if platform:
            query += " AND LOWER(platform) = LOWER(?)"
            params.append(platform)

        if country:
            query += " AND UPPER(country) = UPPER(?)"
            params.append(country)

        if search:
            query += " AND LOWER(workflow) LIKE LOWER(?)"
            params.append(f"%{search}%")

        query += " ORDER BY popularity_score DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = []
        conn = self._get_connection()
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                item = {
                    "id": row["id"],
                    "workflow": row["workflow"],
                    "platform": row["platform"],
                    "popularity_score": row["popularity_score"],
                    "popularity_metrics": json.loads(row["metrics_json"]),
                    "country": row["country"]
                }
                if row["source_url"]:
                    item["source_url"] = row["source_url"]
                results.append(item)
        finally:
            if not self._mem_conn:
                conn.close()

        return results

    def get_top_workflows(self, limit: int = 10, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.get_all_workflows(platform=platform, limit=limit)
