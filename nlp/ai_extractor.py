# backend/nlp/ai_extractor.py

import os
import requests
import json

API_URL = "https://api.deepseek.com/chat/completions"

# Prefer dedicated key, but fall back to general DEEPSEEK_API_KEY if needed
DEEPSEEK_EXTRACTION_API_KEY="sk-fdbbc01319c74effbca6cb4c40215e10"


def _require_api_key():
    if not DEEPSEEK_EXTRACTION_API_KEY:
        raise RuntimeError(
            "No DeepSeek key found. Set DEEPSEEK_EXTRACTION_API_KEY or DEEPSEEK_API_KEY."
        )


def extract_analysis_from_ai(article_text: str) -> dict:
    """
    Call DeepSeek and return:
      industry_name, industry_tactic, stakeholders,
      targeted_policy, geographical_focus, outcome_impact
    """
    _require_api_key()

    prompt = f"""
    You are an expert media monitoring analyst.

    Read the article text below and extract these fields as JSON:
    - industry_name (short)
    - industry_tactic (short phrase)
    - stakeholders (list of key actors/organizations)
    - targeted_policy (short phrase, law/policy/issue targeted, if any)
    - geographical_focus (country/region/city)
    - outcome_impact (1–2 sentence description of likely or actual impact)

    Return ONLY valid JSON. No extra commentary.

    Article:
    {article_text}
    """

    resp = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_EXTRACTION_API_KEY}"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )

    print("DeepSeek status:", resp.status_code)  # keep for debugging; remove later

    if resp.status_code != 200:
        raise RuntimeError(
            f"DeepSeek extraction API error: {resp.status_code} {resp.text}"
        )

    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    #Try normal JSON parse
    try:
        return json.loads(content)
    except json.JSONDecodeError:
    #Handle ```json ... ``` wrapping
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        return json.loads(cleaned)
