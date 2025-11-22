from fastapi import APIRouter, HTTPException
from database.connection import get_db
import json
from nlp.insight_engine import generate_project_insights

router = APIRouter(prefix="/project", tags=["Insights"])


# ----------------------------------------------------------
# 1️⃣ GET LATEST INSIGHTS
# ----------------------------------------------------------
@router.get("/{project_id}/insights/latest")
def get_latest_insights(project_id: str):

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM project_insights
        WHERE project_id = %s
        ORDER BY generated_at DESC
        LIMIT 1
    """, (project_id,))

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return {"status": "empty"}

    # Parse JSON fields
    json_fields = [
        "topic_clusters", "subthemes", "sentiment", "entities",
        "risk_scoring", "opportunity_scoring", "highlights"
    ]

    for key in json_fields:
        if key in row and isinstance(row[key], str):
            try:
                row[key] = json.loads(row[key])
            except:
                row[key] = None

    return row


# ----------------------------------------------------------
# 2️⃣ MANUAL GENERATOR
# ----------------------------------------------------------
@router.post("/{project_id}/insights/generate")
def generate_insights_now(project_id: str):
    try:
        resp = generate_project_insights(project_id)
        return {"status": "success", "result": resp}
    except Exception as e:
        print("Insight generation failed:", e)
        raise HTTPException(status_code=500, detail="Insight generation failed")
