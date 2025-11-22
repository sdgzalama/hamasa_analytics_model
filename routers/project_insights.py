from fastapi import APIRouter, HTTPException
from database.connection import get_db
from nlp.insight_engine import generate_project_insights

router = APIRouter(prefix="/project", tags=["Project Insights"])


@router.get("/{project_id}/insights/latest")
def get_latest_insight(project_id: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM project_insights
        WHERE project_id = %s
        ORDER BY generated_at DESC
        LIMIT 1
    """, (project_id,))

    insight = cursor.fetchone()
    cursor.close()
    conn.close()

    if not insight:
        return {"status": "empty"}

    return insight


@router.post("/{project_id}/insights/generate")
def generate_insight_manual(project_id: str):
    result = generate_project_insights(project_id)
    return result
