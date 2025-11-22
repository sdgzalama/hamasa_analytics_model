# backend/nlp/semantic_generator.py

import uuid
from openai import OpenAI
from database.connection import get_db

client_ai = OpenAI()

SYSTEM_PROMPT = """
You are an expert analyst in media monitoring, public policy, governance,
and corporate industry interference. Your job is to generate a list of 
semantic thematic areas for a project based on its title and description.

Rules:
- Return ONLY a JSON array of objects: [{ "name": "...", "description": "..." }]
- 5 to 12 thematic areas.
- Thematic areas must be specific and actionable.
- Avoid generic themes like "general news".
- Focus on policy, actors, influence, narratives, and manipulation patterns.
"""


def generate_semantic_areas(project_id: str, title: str, description: str):
    """
    Generates semantic areas using AI and stores them in the DB.
    Returns the list of inserted semantic areas.
    """

    # -----------------------------------------
    # 1. Generate using OpenAI
    # -----------------------------------------
    response = client_ai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"PROJECT TITLE: {title}\nDESCRIPTION: {description}"
            }
        ],
        temperature=0.3
    )

    try:
        thematic_list = eval(response.choices[0].message.content)
    except Exception as e:
        raise ValueError(f"Invalid AI output format: {str(e)}")

    # -----------------------------------------
    # 2. Insert into database
    # -----------------------------------------
    conn = get_db()
    cursor = conn.cursor()

    sql = """
        INSERT INTO thematic_areas (id, project_id, name, description)
        VALUES (%s, %s, %s, %s)
    """

    inserted = []

    for item in thematic_list:
        theme_id = str(uuid.uuid4())
        cursor.execute(sql, (
            theme_id,
            project_id,
            item["name"],
            item["description"]
        ))
        inserted.append({
            "id": theme_id,
            "name": item["name"],
            "description": item["description"]
        })

    conn.commit()
    cursor.close()
    conn.close()

    return inserted
