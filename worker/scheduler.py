# scheduler 
import time
import threading
from database.connection import get_db
import requests
import os

API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def process_one_item():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id FROM media_items
        WHERE analysis_status = 'raw'
        ORDER BY scraped_at ASC
        LIMIT 1
    """)

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return

    media_id = row["id"]

    print(f"[SCHEDULER] Processing one item: {media_id}")
    try:
        requests.post(f"{API_URL}/process/media-item/{media_id}")
    except Exception as e:
        print("Scheduler error:", e)

def start_scheduler():

    def delayed_start():
        time.sleep(5)  # allow FastAPI to fully start
        loop()

    def loop():
        while True:
            process_one_item()
            time.sleep(600)  # every 10 minutes

    thread = threading.Thread(target=delayed_start, daemon=True)
    thread.start()

