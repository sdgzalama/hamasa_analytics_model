from fastapi import APIRouter, HTTPException
from database.connection import get_db

router = APIRouter(prefix="/project", tags=["Project Dashboard"])


@router.get("/{project_id}/dashboard")
def project_dashboard(project_id: str):
    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # ------------------------------------------------------
        # 1. PROJECT DETAILS
        # ------------------------------------------------------
        cursor.execute("""
            SELECT 
                p.id,
                p.title,
                p.description,
                c.name AS client_name
            FROM projects p
            LEFT JOIN clients c ON p.client_id = c.id
            WHERE p.id = %s
        """, (project_id,))
        
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # ------------------------------------------------------
        # 2. BASE METRICS
        # ------------------------------------------------------
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_items,
                SUM(CASE WHEN m.analysis_status = 'extracted' THEN 1 ELSE 0 END) AS extracted_items,
                SUM(CASE WHEN m.analysis_status = 'raw' THEN 1 ELSE 0 END) AS awaiting_items
            FROM media_items m
            JOIN project_media_items pmi 
                ON pmi.media_item_id = m.id
            WHERE pmi.project_id = %s
        """, (project_id,))
        
        stats = cursor.fetchone() or {
            "total_items": 0,
            "extracted_items": 0,
            "awaiting_items": 0
        }

        # ------------------------------------------------------
        # 3. THEMATIC AREA DISTRIBUTION (based on semantic matches)
        # ------------------------------------------------------
        cursor.execute("""
            SELECT 
                t.name AS name,
                COUNT(*) AS count
            FROM media_items m
            JOIN project_media_items pmi 
                ON pmi.media_item_id = m.id
            JOIN thematic_areas t
                ON FIND_IN_SET(t.id, m.semantic_area_ids)
            WHERE pmi.project_id = %s
            GROUP BY t.name
            ORDER BY count DESC
        """, (project_id,))
        
        theme_distribution = cursor.fetchall() or []

        # ------------------------------------------------------
        # 4. RELEVANT MEDIA ITEMS (from AI relevance tagging)
        # ------------------------------------------------------
        cursor.execute("""
            SELECT 
                m.id,
                m.raw_title,
                m.analysis_summary,
                m.url,
                m.published_at,
                s.name AS source_name
            FROM media_items m
            JOIN project_media_items pmi 
                ON pmi.media_item_id = m.id
            JOIN media_sources s 
                ON s.id = m.source_id
            WHERE pmi.project_id = %s
              AND m.is_relevant = 1
            ORDER BY m.published_at DESC
        """, (project_id,))
        
        relevant_items = cursor.fetchall() or []

        # ------------------------------------------------------
        # FINAL DASHBOARD RESPONSE
        # ------------------------------------------------------
        return {
            "project": {
                "id": project["id"],
                "title": project["title"],
                "description": project.get("description"),
                "client_name": project.get("client_name")
            },
            "stats": {
                "total_items": stats["total_items"],
                "extracted_items": stats["extracted_items"],
                "awaiting_items": stats["awaiting_items"]
            },
            "themes": theme_distribution,
            "relevant_items": relevant_items
        }

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
