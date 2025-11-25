from fastapi import APIRouter, HTTPException
from database.connection import get_db
from formatters.media_output import format_media_output
from project_loader import load_project_details

router = APIRouter(prefix="/project", tags=["Project Reports"])

@router.get("/{project_id}/reports")
def get_project_reports(project_id: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # 1. Get all media items linked to this project
    cursor.execute("""
        SELECT m.*, s.name AS source_name
        FROM media_items m
        JOIN project_media_items pmi ON pmi.media_item_id = m.id
        JOIN media_sources s ON s.id = m.source_id
        WHERE pmi.project_id = %s
        ORDER BY m.scraped_at DESC
    """, (project_id,))
    media_items = cursor.fetchall()

    # 2. Load analysis for all items
    reports = []
    project = load_project_details(project_id)

    for item in media_items:
        cursor.execute("""
            SELECT *
            FROM media_item_project_analysis
            WHERE media_item_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (item["id"],))
        analysis = cursor.fetchone()

        if analysis:
            reports.append(format_media_output(item, analysis, project))

    cursor.close()
    conn.close()

    return {"project_id": project_id, "count": len(reports), "items": reports}
