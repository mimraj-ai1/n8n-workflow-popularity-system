"""
run_tests.py — Quick smoke tests for the n8n Workflow Popularity System.
Validates that all modules import correctly, storage works, scoring works,
and collectors can be instantiated.
"""
import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  [PASS] {name}")
        passed += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        failed += 1


print("\n=== n8n Workflow Popularity System — Smoke Tests ===\n")

# ── 1. Module imports ────────────────────────────────────────────────────────
print("[1] Module Imports")
test("Import base WorkflowEntry",
     lambda: __import__("src.collectors.base", fromlist=["WorkflowEntry"]))
test("Import YouTubeCollector",
     lambda: __import__("src.collectors.youtube_collector", fromlist=["YouTubeCollector"]))
test("Import ForumCollector",
     lambda: __import__("src.collectors.forum_collector", fromlist=["ForumCollector"]))
test("Import GoogleTrendsCollector",
     lambda: __import__("src.collectors.google_trends_collector", fromlist=["GoogleTrendsCollector"]))
test("Import PopularityCalculator",
     lambda: __import__("src.scoring.popularity_calculator", fromlist=["PopularityCalculator"]))
test("Import WorkflowStorage",
     lambda: __import__("src.storage.db", fromlist=["WorkflowStorage"]))
test("Import FastAPI app",
     lambda: __import__("src.api.main", fromlist=["app"]))
test("Import scheduler",
     lambda: __import__("src.scheduler.cron", fromlist=["run_scheduled_pipeline"]))

# ── 2. Scoring engine ───────────────────────────────────────────────────────
print("\n[2] Scoring Engine")
from src.scoring.popularity_calculator import PopularityCalculator

def test_youtube_score():
    score = PopularityCalculator.calculate_youtube_score(10000, 500, 50)
    assert 0 <= score <= 100, f"Score out of range: {score}"

def test_forum_score():
    score = PopularityCalculator.calculate_forum_score(5000, 100, 80)
    assert 0 <= score <= 100, f"Score out of range: {score}"

def test_trends_score():
    score = PopularityCalculator.calculate_google_trends_score(75.0, 10.0)
    assert 0 <= score <= 100, f"Score out of range: {score}"

def test_zero_views():
    assert PopularityCalculator.calculate_youtube_score(0, 0, 0) == 0.0

test("YouTube score in 0-100", test_youtube_score)
test("Forum score in 0-100", test_forum_score)
test("Google Trends score in 0-100", test_trends_score)
test("Zero views returns 0.0", test_zero_views)

# ── 3. Storage (in-memory) ──────────────────────────────────────────────────
print("\n[3] SQLite Storage (in-memory)")
from src.storage.db import WorkflowStorage
from src.collectors.base import WorkflowEntry

def test_storage_roundtrip():
    db = WorkflowStorage(db_path=":memory:")
    entry = WorkflowEntry(
        id="test_1", workflow="Test Workflow", platform="YouTube",
        popularity_metrics={"views": 100, "likes": 10, "comments": 5},
        country="US", popularity_score=42.5, source_url="https://example.com"
    )
    saved = db.save_workflows([entry])
    assert saved == 1, f"Expected 1 saved, got {saved}"
    results = db.get_all_workflows()
    assert len(results) == 1, f"Expected 1 result, got {len(results)}"
    assert results[0]["workflow"] == "Test Workflow"

def test_storage_filters():
    db = WorkflowStorage(db_path=":memory:")
    entries = [
        WorkflowEntry(id="yt_1", workflow="YT Flow", platform="YouTube",
                       popularity_metrics={"views": 50}, country="US", popularity_score=80.0),
        WorkflowEntry(id="f_1", workflow="Forum Flow", platform="Forum",
                       popularity_metrics={"views": 30}, country="IN", popularity_score=40.0),
    ]
    db.save_workflows(entries)
    yt = db.get_all_workflows(platform="YouTube")
    assert len(yt) == 1 and yt[0]["platform"] == "YouTube"
    top = db.get_top_workflows(limit=1)
    assert len(top) == 1 and top[0]["popularity_score"] == 80.0

test("Save and retrieve workflow", test_storage_roundtrip)
test("Platform/score filters work", test_storage_filters)

# ── 4. Collector instantiation ──────────────────────────────────────────────
print("\n[4] Collector Instantiation")
from src.collectors.youtube_collector import YouTubeCollector
from src.collectors.forum_collector import ForumCollector
from src.collectors.google_trends_collector import GoogleTrendsCollector

test("YouTubeCollector()", lambda: YouTubeCollector())
test("ForumCollector()", lambda: ForumCollector())
test("GoogleTrendsCollector()", lambda: GoogleTrendsCollector())

# ── Summary ─────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'='*50}")
if failed > 0:
    print("  Some tests FAILED. Please check the errors above.")
    sys.exit(1)
else:
    print("  All tests PASSED! System is ready.")
    sys.exit(0)
