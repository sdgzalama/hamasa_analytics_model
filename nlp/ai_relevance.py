# backend/nlp/ai_relevance.py

import os
import json
import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

def _call_deepseek(prompt: str):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }

    res = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=60)
    if res.status_code != 200:
        raise RuntimeError(f"DeepSeek Error: {res.status_code} {res.text}")

    content = res.json()["choices"][0]["message"]["content"]

    # Normalize JSON
    try:
        return json.loads(content)
    except Exception:
        content = content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)


def ai_relevance_check(project_title: str, project_desc: str, title: str, body: str):
    """Returns: {relevant: bool, confidence: int, reason: str}"""

    preview = (body or "")[:1200]

    prompt = f"""
You are a relevance classifier.

PROJECT:
Title: {project_title}
Description: {project_desc}

ARTICLE:
Title: {title}
Body: {preview}

Task: Decide if this article is relevant to the project.

Return ONLY JSON:
{{
  "relevant": true/false,
  "confidence": 0-100,
  "reason": "short explanation"
}}
"""

    return _call_deepseek(prompt)
