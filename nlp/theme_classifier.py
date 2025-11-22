# Theme classifier 
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def classify_into_thematic_areas(article_text: str, thematic_areas: list):
    """
    thematic_areas = [
        {"id": "...", "name": "...", "description": "..."},
        ...
    ]
    Returns: list of thematic_area IDs
    """

    themes_text = "\n".join([
        f"- {t['id']} — {t['name']}: {t['description']}"
        for t in thematic_areas
    ])

    prompt = f"""
Analyze the article and determine which thematic areas it belongs to.

Return ONLY a JSON array of IDs.

Themes:
{themes_text}

Article:
{article_text}

Respond ONLY in strict JSON:
["theme_id_1", "theme_id_3"]
"""

    try:
        response = client.chat.completions.create(
            model="google/gemma-3-4b-it:free",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        return json.loads(raw)

    except Exception as e:
        print("\n🔥 THEME CLASSIFICATION ERROR 🔥")
        print(e)
        return []
