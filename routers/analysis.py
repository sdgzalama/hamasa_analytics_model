from fastapi import APIRouter, HTTPException
from database.connection import get_db
from nlp.ai_extractor import extract_analysis_from_ai
from nlp.theme_classifier import classify_into_thematic_areas
from nlp.ai_relevance import ai_relevance_check
import uuid
import json

router = APIRouter(prefix="/process", tags=["AI Processing"])


@router.post("/media-item/{media_id}")
def process_media_item(media_id: str):

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch media item
    cursor.execute("""
        SELECT m.*, s.name AS source_name
        FROM media_items m
        JOIN media_sources s ON s.id = m.source_id
        WHERE m.id=%s
    """, (media_id,))
    item = cursor.fetchone()

    if not item:
        raise HTTPException(404, "Media item not found")

    article_text = item["raw_text"] or item["raw_title"]

    # 2. Get linked projects
    cursor.execute("""
        SELECT project_id 
        FROM project_media_items
        WHERE media_item_id=%s
    """, (media_id,))
    projects = cursor.fetchall()

    if not projects:
        raise HTTPException(400, "Item not linked to any project")

    # 3. Extract fields
    ai_fields = extract_analysis_from_ai(article_text)
    for f in [
        "industry_name", "industry_tactic", "stakeholders",
        "targeted_policy", "geographical_focus", "outcome_impact"
    ]:
        ai_fields.setdefault(f, "")

    stakeholders_str = (
        ", ".join(ai_fields["stakeholders"])
        if isinstance(ai_fields["stakeholders"], list)
        else str(ai_fields["stakeholders"])
    )

    # 4. For each project → compute & save analysis
    final_relevant = False
    results = {}

    for p in projects:
        pid = p["project_id"]

        # Load project details
        cursor.execute("SELECT title, description FROM projects WHERE id=%s", (pid,))
        project = cursor.fetchone()

        # AI relevance
        ai_rel = ai_relevance_check(
            project["title"],
            project["description"] or "",
            item["raw_title"],
            article_text,
        )

        # Load thematic areas for this project
        cursor.execute("""
            SELECT id, name, description
            FROM thematic_areas
            WHERE project_id=%s
        """, (pid,))
        themes = cursor.fetchall()

        matched_ids = classify_into_thematic_areas(article_text, themes)

        matched_meta = [
            {"id": t["id"], "name": t["name"]}
            for t in themes if t["id"] in matched_ids
        ]

        # Determine relevance
        theme_relevant = len(matched_ids) > 0
        hybrid_relevant = ai_rel["relevant"] and theme_relevant

        if hybrid_relevant:
            final_relevant = True

        # Build summary text
        if matched_meta:
            theme_names = ", ".join([t["name"] for t in matched_meta])
            summary = (
                f"'{item['raw_title']}' from {item['source_name']} covers "
                f"{ai_fields['industry_name']} in {ai_fields['geographical_focus']}. "
                f"It is relevant to these thematic areas: {theme_names}."
            )
        else:
            summary = (
                f"'{item['raw_title']}' from {item['source_name']} covers "
                f"{ai_fields['industry_name']} in {ai_fields['geographical_focus']}. "
                f"However, it does not match any thematic areas for this project."
            )

        # Save analysis row
        analysis_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO media_item_project_analysis (
                id, media_item_id, project_id,
                relevant, relevance_confidence, relevance_reason,
                semantic_area_ids, matched_thematic_areas,
                ai_fields, summary
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            analysis_id,
            media_id,
            pid,

            hybrid_relevant,
            ai_rel.get("confidence", 0),
            ai_rel.get("reason", ""),

            json.dumps(matched_ids),
            json.dumps(matched_meta),
            json.dumps(ai_fields),
            summary
        ))

        results[pid] = {
            "relevant": hybrid_relevant,
            "confidence": ai_rel.get("confidence"),
            "reason": ai_rel.get("reason"),
            "matched_thematic_areas": matched_meta,
            "ai_fields": ai_fields,
            "semantic_area_ids": matched_ids,
            "summary": summary
        }

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "status": "success",
        "media_id": media_id,
        "final_relevant": final_relevant,
        "per_project_results": results
    }
