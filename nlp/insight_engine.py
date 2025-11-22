import uuid
import json
import os
import requests
from datetime import datetime
from database.connection import get_db

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ---------------------------------------------------------
# SAFE API CALL
# ---------------------------------------------------------

def deepseek_request(prompt: str, json_expected=True):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }

    if json_expected:
        payload["response_format"] = {"type": "json_object"}

    res = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=60)

    if res.status_code != 200:
        raise Exception(f"DeepSeek API Error: {res.status_code} {res.text}")

    content = res.json()["choices"][0]["message"]["content"]

    if json_expected:
        try:
            return json.loads(content)
        except:
            # fix cases where model wraps in ```json
            cleaned = content.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)

    return content


# ---------------------------------------------------------
# STEP 1 — RELEVANCE CHECK FOR EACH ARTICLE
# ---------------------------------------------------------
def ai_check_relevance(project_title: str, project_desc: str, article_title: str, article_body: str):
    prompt = f"""
You are a classifier.

Project Title: {project_title}
Project Description: {project_desc}

Article:
TITLE: {article_title}
BODY: {article_body[:1500]}

Determine if this article is relevant to the project.
Return ONLY JSON:

{{
  "relevant": true | false,
  "reason": "short explanation"
}}
"""

    return deepseek_request(prompt, json_expected=True)


# ---------------------------------------------------------
# STEP 2 — AI INSIGHT GENERATION BASED ON RELEVANT ARTICLES
# ---------------------------------------------------------
def ai_generate_insight(project_title, project_desc, articles):
    block = ""
    for art in articles:
        text_preview = (art["raw_text"] or "")[:3500]
        block += f"""
### ARTICLE
ID: {art['id']}
Title: {art['raw_title']}
URL: {art['url']}
Content: {text_preview}
"""

    prompt = f"""
You are a top-tier geopolitical & policy intelligence analyst.

TASK:
Synthesize ALL articles into a structured intelligence report.
Provide multi-layer reasoning, extraction of deeper signals, and
project-specific strategic insights.

PROJECT
Title: {project_title}
Description: {project_desc}

ARTICLES
{block}

Return ONLY JSON with:

{{
  "executive_summary": "",
  "strategic_assessment": "",
  "key_themes": [],
  "emerging_signals": [],
  "risks": [],
  "opportunities": [],
  "long_term_implications": [],
  "narratives": [],
  "bias_detection": [],
  "sentiment": {{
      "positive": 0,
      "negative": 0,
      "neutral": 0
  }},
  "entity_map": {{
      "people": [],
      "organizations": [],
      "locations": []
  }},
  "article_links": [],
  "recommendations": [],
  "highlights": []
}}
"""

    return deepseek_request(prompt, json_expected=True)



# ---------------------------------------------------------
# STEP 3 — MAIN PIPELINE
# ---------------------------------------------------------
def generate_project_insights(project_id: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # -------------------------------
    # Load project
    # -------------------------------
    cursor.execute("""
        SELECT title, description
        FROM projects
        WHERE id=%s
    """, (project_id,))
    project = cursor.fetchone()

    if not project:
        return {"status": "error", "detail": "Project not found"}

    p_title = project["title"]
    p_desc = project.get("description") or ""

    # -------------------------------
    # Load linked articles
    # -------------------------------
    cursor.execute("""
        SELECT m.id, m.raw_title, m.raw_text, m.url
        FROM media_items m
        JOIN project_media_items pmi ON pmi.media_item_id = m.id
        WHERE pmi.project_id=%s
    """, (project_id,))
    articles = cursor.fetchall()

    if not articles:
        return {"status": "ok", "relevant_count": 0, "insight": None}

    # -------------------------------
    # STEP 1 — Relevance Classification
    # -------------------------------
    relevant_articles = []

    for art in articles:
        try:
            result = ai_check_relevance(
                p_title, p_desc, art["raw_title"], art["raw_text"]
            )
            relevant = result["relevant"]

            # Update DB
            cursor.execute(
                "UPDATE media_items SET is_relevant=%s WHERE id=%s",
                (1 if relevant else 0, art["id"]),
            )

            if relevant:
                relevant_articles.append(art)

        except Exception as e:
            print("Relevance error:", e)

    conn.commit()

    # If no relevant articles, save empty insight entry
    if len(relevant_articles) == 0:
        insight_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO project_insights (id, project_id, executive_summary)
            VALUES (%s, %s, %s)
        """, (insight_id, project_id, "No relevant articles found."))
        conn.commit()
        return {"status": "ok", "relevant_count": 0, "insight": None}

    # -------------------------------
    # STEP 2 — Generate overall insights
    # -------------------------------
    ai_result = ai_generate_insight(p_title, p_desc, relevant_articles)

    insight_id = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO project_insights (
            id, project_id, generated_at,
            executive_summary, key_themes, narratives,
            risks, opportunities, sentiment, entity_map,
            article_links, recommendations, highlights
        ) VALUES (%s, %s, NOW(),
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s)
    """, (
        insight_id,
        project_id,
        ai_result["executive_summary"],
        json.dumps(ai_result["key_themes"]),
        json.dumps(ai_result["narratives"]),
        json.dumps(ai_result["risks"]),
        json.dumps(ai_result["opportunities"]),
        json.dumps(ai_result["sentiment"]),
        json.dumps(ai_result["entity_map"]),
        json.dumps(ai_result["article_links"]),
        json.dumps(ai_result["recommendations"]),
        json.dumps(ai_result["highlights"]),
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return {
        "status": "ok",
        "insight_id": insight_id,
        "relevant_count": len(relevant_articles),
        "ai_result": ai_result
    }
