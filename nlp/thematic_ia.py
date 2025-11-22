import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

def generate_thematic_areas_ai(title: str, description: str):
    prompt = f"""
    Generate 5 thematic areas for a media monitoring project.

    PROJECT TITLE:
    {title}

    PROJECT DESCRIPTION:
    {description}

    Return CLEAN JSON in this format:

    [
      {{
        "name": "",
        "description": ""
      }}
    ]
    """

    try:
        response = client.chat.completions.create(
            model="google/gemma-3-4b-it:free",
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1].replace("json", "").strip()

        return json.loads(raw)

    except Exception as e:
        print("AI THEMATIC ERROR:", e)
        return None
