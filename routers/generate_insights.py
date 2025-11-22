# backend/routers/project_insights.py

from fastapi import APIRouter, HTTPException
from database.connection import get_db
from uuid import uuid4
import os
import requests

router = APIRouter(prefix="/project", tags=["Project Insights"])

# Get API key from environment
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def _require_api_key():
    if not DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="DEEPSEEK_API_KEY is not set on the server."
        )


@router.post("/{project_id}/insights/generate")
def generate_project_insights(project_id: str):
    """
    Generate insights for a single project by summarizing
    all its linked media items using DeepSeek.
    """

    _require_api_key()

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Get project name & description
        cursor.execute(
            "SELECT title, description FROM projects WHERE id=%s",
            (project_id,),
        )
        project = cursor.fetchone()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # 2. Get media items linked to this project
        cursor.execute(
            """
            SELECT m.id, m.raw_title, m.raw_text, m.url
            FROM media_items m
            JOIN project_media_items pmi ON pmi.media_item_id = m.id
            WHERE pmi.project_id = %s
            """,
            (project_id,),
        )
        items = cursor.fetchall()

        if not items:
            raise HTTPException(
                status_code=400,
                detail="No media items found for this project",
            )

        # 3. Build combined context for the LLM
        combined_text_parts = []
        for item in items:
            text_preview = (item["raw_text"] or "")[:2000]
            combined_text_parts.append(
                f"\n---\nTitle: {item['raw_title']}\nURL: {item['url']}\nText: {text_preview}\n"
            )

        combined_text = "".join(combined_text_parts)

        # 4. Prompt for DeepSeek
        prompt = f"""
        Project Title: {project['title']}
        Project Description: {project.get('description') or ''}

        Below is a collection of media articles related to this project.

        For ALL the articles combined, provide a structured insight report with:

        - Executive Summary (short, 2–3 paragraphs)
        - Key Themes (bullet list)
        - Sentiment Overview (overall tone, with explanation)
        - Risks (bullet list, link them to specific article URLs where possible)
        - Opportunities (bullet list, link them to specific article URLs where possible)
        - Recommendations (concrete next steps for the client)
        - For each key insight, mention which article URL(s) contributed to it.

        Articles:
        {combined_text}
        """

        # 5. Call DeepSeek API
        try:
            response = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
        except requests.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"Error calling DeepSeek API: {str(e)}",
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"DeepSeek API error: {response.status_code} {response.text}",
            )

        data = response.json()
        try:
            ai_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise HTTPException(
                status_code=502,
                detail="Unexpected response format from DeepSeek API",
            )

        # 6. Save insights into project_insights table
        insight_id = str(uuid4())

        # Store whole AI report in executive_summary for now
        cursor.execute(
            """
            INSERT INTO project_insights (id, project_id, executive_summary)
            VALUES (%s, %s, %s)
            """,
            (insight_id, project_id, ai_text),
        )

        conn.commit()

        return {
            "status": "ok",
            "project_id": project_id,
            "insight_id": insight_id,
            "insights": ai_text,
        }

    finally:
        cursor.close()
        conn.close()


@router.get("/{project_id}/insights/latest")
def get_latest_insight(project_id: str):
    """
    Return the latest generated insight for a project.
    """

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT id, project_id, generated_at, executive_summary
            FROM project_insights
            WHERE project_id = %s
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (project_id,),
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="No insights found for this project",
            )

        return {
            "insight_id": row["id"],
            "project_id": row["project_id"],
            "generated_at": row["generated_at"],
            "executive_summary": row["executive_summary"],
        }

    finally:
        cursor.close()
        conn.close()
