# BACKEND/ROUTERS/ITEMS.PY

from fastapi import APIRouter, BackgroundTasks, HTTPException
from database.connection import get_db
from worker.task_queue import queue_bulk_processing, get_progress

router = APIRouter(prefix="/media", tags=["Media Items"])


# -----------------------------------------------------
# 1. GET — LIST MEDIA ITEMS
# -----------------------------------------------------
@router.get("/")
def list_media_items():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            m.id,
            m.raw_title,
            LEFT(m.raw_text, 120) AS preview,
            m.url AS url,
            m.analysis_status,
            m.scraped_at,
            s.name AS source_name
        FROM media_items m
        LEFT JOIN media_sources s ON m.source_id = s.id
        ORDER BY m.scraped_at DESC
    """)

    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items


# -----------------------------------------------------
# 2. PROCESS ALL RAW ITEMS (BULK)
# -----------------------------------------------------
@router.post("/process/all")
def process_all_items(background: BackgroundTasks):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id FROM media_items WHERE analysis_status = 'raw'")
    items = cursor.fetchall()

    ids = [row["id"] for row in items]

    queue_bulk_processing(background, ids)

    cursor.close()
    conn.close()

    return {
        "status": "queued",
        "total": len(ids),
        "message": "Processing started in background"
    }


# -----------------------------------------------------
# 3. GET — LATEST 10 ITEMS
# -----------------------------------------------------
@router.get("/latest/10")
def latest_media_items():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT 
            m.id,
            LEFT(m.raw_text, 60) AS title,
            m.analysis_status,
            s.name AS media_source_name
        FROM media_items m
        JOIN media_sources s ON m.source_id = s.id
        ORDER BY m.scraped_at DESC
        LIMIT 10
    """)
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items


# -----------------------------------------------------
# 4. BULK PROCESSING PROGRESS
# -----------------------------------------------------
@router.get("/progress")
def get_processing_progress():
    return get_progress()


# -----------------------------------------------------
# 5. GET SINGLE MEDIA ITEM + ALL PROJECT ANALYSIS
# -----------------------------------------------------
@router.get("/{media_id}")
def get_media_item(media_id: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # ---- Fetch base media item
    cursor.execute("""
        SELECT m.*, s.name AS source_name
        FROM media_items m
        JOIN media_sources s ON s.id = m.source_id
        WHERE m.id = %s
    """, (media_id,))
    item = cursor.fetchone()

    if not item:
        raise HTTPException(404, "Media item not found")

    # ---- Fetch per-project AI analysis
    cursor.execute("""
        SELECT *
        FROM media_item_project_analysis
        WHERE media_item_id = %s
        ORDER BY created_at DESC
    """, (media_id,))
    analyses = cursor.fetchall()

    cursor.close()
    conn.close()

    # Final response
    return {
        **item,
        "project_analysis": analyses
    }
