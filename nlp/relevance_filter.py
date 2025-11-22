import os
import requests
from sentence_transformers import SentenceTransformer, util

# -------------------------------------------------------------------
# LOAD EMBEDDING MODEL (only once)
# -------------------------------------------------------------------
embedder = SentenceTransformer("all-MiniLM-L6-v2")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


# ===================================================================
# 1) OPTIONAL — LLM Relevance Confirmation
# ===================================================================
def llm_relevancy_check(project_title: str, project_description: str, article: dict) -> bool:
    """
    Uses DeepSeek to verify relevance.
    Returns:
        True → article is relevant
        False → irrelevant
    """
    if not DEEPSEEK_API_KEY:
        # Safe fallback: rely on embeddings only
        return True

    body_preview = (article.get("raw_text") or "")[:800]

    question = f"""
Project Title: {project_title}
Project Description: {project_description}

Article Title: {article.get("raw_title", "")}
Article Body: {body_preview}

Question:
Is this article related to the project?
Answer STRICTLY with: YES or NO.
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    payload = {
        "model": "deepseek-v2",
        "messages": [
            {"role": "system", "content": "You check if an article is relevant to a project."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.0
    }

    try:
        res = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=20)

        if res.status_code != 200:
            print("DeepSeek error:", res.text)
            return True  # fail-open: do not block relevance

        data = res.json()
        answer = data["choices"][0]["message"]["content"].strip().upper()

        return answer == "YES"

    except Exception as e:
        print("LLM relevancy check failed:", e)
        return True  # fail-open safe fallback


# ===================================================================
# 2) MAIN BALANCED RELEVANCE FILTER (R2 ENGINE)
# ===================================================================
def filter_relevant_articles(project_title: str, project_description: str, articles: list) -> list:
    """
    Combined Embedding + Optional LLM relevance filter.
    Returns only relevant articles.
    """

    # Build reference embedding
    project_text = f"{project_title} {project_description}".strip()
    project_embed = embedder.encode(project_text, convert_to_tensor=True)

    relevant_articles = []

    for article in articles:
        raw_title = article.get("raw_title") or ""
        raw_text = article.get("raw_text") or ""

        # Skip empty articles immediately
        if not raw_text.strip() and not raw_title.strip():
            continue

        full_text = f"{raw_title} {raw_text}".strip()

        # ------------------------------
        # 1) Embedding similarity check
        # ------------------------------
        try:
            article_embed = embedder.encode(full_text, convert_to_tensor=True)
            similarity = float(util.cos_sim(project_embed, article_embed)[0])
        except Exception:
            # Skip broken encoding
            continue

        # Balanced threshold (empirically good)
        if similarity < 0.38:
            continue

        # ------------------------------
        # 2) Keyword weak signal (optional)
        # ------------------------------
        if project_title.lower() in full_text.lower():
            keyword_match = True
        else:
            keyword_match = False  # acceptable, embedding already passed

        # ------------------------------
        # 3) Optional LLM confirmation
        # ------------------------------
        if not llm_relevancy_check(project_title, project_description, article):
            continue

        # If all checks passed
        relevant_articles.append(article)

    return relevant_articles
