import json

def format_media_output(media_item, analysis, project):
    thematic_name = ""
    thematic_description = ""

    # 1. Extract thematic area info
    matched = analysis.get("matched_thematic_areas")

    if isinstance(matched, str):
        try:
            matched = json.loads(matched)
        except:
            matched = []

    if matched and len(matched) > 0:
        thematic_id = matched[0].get("id")
        for t in project["thematic_areas"]:
            if t["id"] == thematic_id:
                thematic_name = t["name"]
                thematic_description = t["description"]
                break
    else:
        thematic_name = "AI FOUND NO MATCH"
        thematic_description = "AI did not classify this article into any thematic area"

    # 2. Media category
    source_name = media_item["source_name"]
    media_category = "Unknown"
    for s in project["media_sources"]:
        if s["id"] == media_item["source_id"] or s["name"] == source_name:
            media_category = s["type"]
            break

    # 3. Determine media format
    url = media_item["url"] or ""
    media_format = "video" if "youtube.com" in url else "article"

    # 4. Final structure
    return {
        "id": media_item["id"],
        "date": str(media_item["scraped_at"]),
        "title": media_item["raw_title"],
        "content": media_item["raw_text"],
        "source": source_name,
        "media_category": media_category,
        "media_format": media_format,
        "thematic_area": thematic_name,
        "thematic_description": thematic_description,
        "objectives": [],
        "link": url,
        "status": "Verified" if analysis["relevant"] else "Unverified",
    }
