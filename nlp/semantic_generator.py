# backend/nlp/semantic_generator.py

import uuid
import json
import os
from openai import OpenAI
from database.connection import get_db

# Configure OpenRouter
client_ai = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

SYSTEM_PROMPT = """
You are an expert analyst in media monitoring and policy interference.
Generate HIGH-QUALITY thematic areas from a project's title and description.

Rules:
- Return ONLY a JSON array of objects.
- Each object: { "name": "...", "description": "..." }
- 5 to 12 items.
- No generic themes.
- Must be specific, policy-driven, actionable.
"""


def generate_semantic_areas(project_id: str, title: str, description: str):
    # -------------------------------
    # 1. Build unified prompt
    # -------------------------------

    prompt = f"""
{SYSTEM_PROMPT}

PROJECT TITLE: {title}
DESCRIPTION: {description}

Return ONLY pure JSON array.
"""

    # -------------------------------
    # 2. Call OpenRouter (Gemma)
    # -------------------------------
    response = client_ai.chat.completions.create(
        model="google/gemma-3-4b-it:free",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()

    # Remove markdown fencing if present
    if raw.startswith("```"):
        raw = raw.split("```")[1].replace("json", "").strip()

    try:
        thematic_list = json.loads(raw)
    except Exception as e:
        raise ValueError(f"Invalid AI output format: {raw}")

    # -------------------------------
    # 3. Insert into DB
    # -------------------------------
    conn = get_db()
    cursor = conn.cursor()

    sql = """
        INSERT INTO thematic_areas (id, project_id, name, description)
        VALUES (%s, %s, %s, %s)
    """

    inserted = []

    for item in thematic_list:
        theme_id = str(uuid.uuid4())
        cursor.execute(sql, (theme_id, project_id, item["name"], item["description"]))

        inserted.append({
            "id": theme_id,
            "name": item["name"],
            "description": item["description"]
        })

    conn.commit()
    cursor.close()
    conn.close()

    return inserted
