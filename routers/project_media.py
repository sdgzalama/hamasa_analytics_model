from fastapi import APIRouter, HTTPException
from database.connection import get_db

router = APIRouter(prefix="/project", tags=["Project Media"])


@router.get("/{project_id}/media/analysed")
def list_project_analysed_media(project_id: str):
    """
    List analysed media items for a project, including:
    - AI extraction fields
    - source (id, name, type, feed_url)
    - matched thematic areas
    - per-article summary if you add it later
    """

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Load project to ensure it exists
        cursor.execute(
            "SELECT id, title FROM projects WHERE id = %s",
            (project_id,),
        )
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 2. Load thematic areas for this project (for name mapping)
        cursor.execute(
            """
            SELECT id, name
            FROM thematic_areas
            WHERE project_id = %s
            """,
            (project_id,),
        )
        thematic_rows = cursor.fetchall()
        thematic_by_id = {row["id"]: row["name"] for row in thematic_rows}

        # 3. Load analysed media items linked to this project + their source
        cursor.execute(
            """
            SELECT
                m.id,
                m.raw_title,
                m.url,
                m.published_at,
                m.scraped_at,
                m.industry_name,
                m.industry_tactic,
                m.stakeholders,
                m.targeted_policy,
                m.geographical_focus,
                m.outcome_impact,
                m.semantic_area_ids,
                m.analysis_status,
                s.id   AS source_id,
                s.name AS source_name,
                s.type AS source_type,
                s.base_url AS source_feed_url
            FROM media_items m
            JOIN project_media_items pmi ON pmi.media_item_id = m.id
            JOIN media_sources s ON s.id = m.source_id
            WHERE pmi.project_id = %s
              AND m.analysis_status = 'extracted'
            ORDER BY m.scraped_at DESC
            """,
            (project_id,),
        )
        rows = cursor.fetchall()

        results = []

        for row in rows:
            # Parse semantic_area_ids -> list of IDs
            matched_ids = []
            if row["semantic_area_ids"]:
                matched_ids = [
                    tid.strip()
                    for tid in row["semantic_area_ids"].split(",")
                    if tid.strip()
                ]

            # Build matched thematic_areas array with id + name
            matched_thematics = [
                {"id": tid, "name": thematic_by_id.get(tid, "")}
                for tid in matched_ids
                if tid in thematic_by_id
            ]

            # Define relevance: relevant if it matched at least one thematic area
            relevant = len(matched_thematics) > 0

            results.append({
                "media_id": row["id"],
                "title": row["raw_title"],
                "url": row["url"],
                "published_at": row["published_at"],
                "scraped_at": row["scraped_at"],
                "project_id": project_id,

                "source": {
                    "id": row["source_id"],
                    "name": row["source_name"],
                    "type": row["source_type"],
                    "feed_url": row["source_feed_url"],
                },

                "industry_name": row["industry_name"],
                "industry_tactic": row["industry_tactic"],
                "stakeholders": row["stakeholders"],
                "targeted_policy": row["targeted_policy"],
                "geographical_focus": row["geographical_focus"],
                "outcome_impact": row["outcome_impact"],

                "relevant": relevant,
                "matched_thematic_areas": matched_thematics,

                # If you later add analysis_summary column, include it here:
                # "summary": row["analysis_summary"],
            })

        return results

    finally:
        cursor.close()
        conn.close()
