# nlp/project_report.py
from nlp.insight_engine import call_deepseek_json
import json


def build_project_report(project, articles):
    articles_json = [
        {
            "id": a["id"],
            "title": a["raw_title"],
            "url": a["url"],
            "summary": a["summary"],
            "relevance": a["relevance_score"]
        }
        for a in articles
    ]

    prompt = f"""
Project: {project['title']}
Description: {project.get('description') or ''}

Relevant Articles JSON:
{json.dumps(articles_json, indent=2)}

Create a unified analysis report with:

- Executive Summary (3 paragraphs)
- Key Themes (list)
- Sentiment Overview (numeric + explanation)
- Risks (with article references)
- Opportunities (with article references)
- Recommendations
- Future Outlook
- Article Contribution Map

Respond ONLY with a JSON object.
"""

    return call_deepseek_json([
        {"role": "system", "content": "You are a media intelligence system."},
        {"role": "user", "content": prompt}
    ])
