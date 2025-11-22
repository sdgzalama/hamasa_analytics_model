from fastapi import BackgroundTasks
from typing import List
import threading
import time

from routers.analysis import process_media_item   # ✅ FIXED IMPORT
from database.connection import get_db

# GLOBAL PROGRESS TRACKER
progress = {
    "running": False,
    "total": 0,
    "done": 0
}


def _run_bulk(ids: List[str]):
    """
    Runs AI processing in a background thread.
    Works with the new multi-project model.
    """
    progress["running"] = True
    progress["total"] = len(ids)
    progress["done"] = 0

    for media_id in ids:
        try:
            # ⭐ NEW: Correct function name for new architecture
            process_media_item(media_id)

        except Exception as e:
            print("AI ERROR processing", media_id, "→", e)

        progress["done"] += 1

        # Small delay to prevent CPU blocking
        time.sleep(0.1)

    progress["running"] = False



def queue_bulk_processing(background: BackgroundTasks, ids: List[str]):
    """
    Schedule background processing of all RAW items.
    """
    if progress["running"]:
        return False  # Already running

    background.add_task(_run_bulk, ids)
    return True



def get_progress():
    """Return live processing progress."""
    return progress
