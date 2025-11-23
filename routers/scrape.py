from fastapi import APIRouter, HTTPException, Query
from scrapers.rss_scraper import scrape_rss
from database.connection import get_db

router = APIRouter(prefix="/scrape", tags=["Scraping"])


@router.post("/rss")
def scrape_rss_endpoint(
    project_id: str = Query(...),
    source_id: str = Query(...)
):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT base_url, name
        FROM media_sources
        WHERE id = %s
    """, (source_id,))
    
    source = cursor.fetchone()
    cursor.close()
    conn.close()

    if not source:
        raise HTTPException(status_code=404, detail="Source ID not found")

    feed_url = source["base_url"]

    if not feed_url:
        raise HTTPException(status_code=400, detail="Source has no RSS URL")

    items = scrape_rss(project_id, source_id, feed_url)

    return {
        "status": "success",
        "source": source["name"],
        "feed_url": feed_url,
        "items": items
    }


@router.get("/run-all")
def run_all_sources():
    """Scrape ALL media sources and all linked projects automatically."""
    
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # 1️⃣ Load all RSS-enabled sources
    cursor.execute("""
        SELECT id, name, base_url AS rss_url
        FROM media_sources
        WHERE base_url IS NOT NULL AND base_url != ''
    """)
    sources = cursor.fetchall()

    if not sources:
        return {"status": "empty", "message": "No RSS sources with base_url found."}

    results = []

    for source in sources:
        source_id = source["id"]
        rss_url = source["rss_url"]

        # 2️⃣ find all projects sharing this source
        cursor.execute("""
            SELECT project_id
            FROM project_media_sources
            WHERE media_source_id = %s
        """, (source_id,))
        
        projects = cursor.fetchall()
        project_ids = [p["project_id"] for p in projects]

        # 3️⃣ scrape for each project
        for pid in project_ids:
            scraped = scrape_rss(pid, source_id, rss_url)
            results.append({
                "source_name": source["name"],
                "project_id": pid,
                "rss_url": rss_url,
                "scrape_result": scraped
            })

    cursor.close()
    conn.close()

    return {
        "status": "ok",
        "total_sources": len(sources),
        "total_scrapes": len(results),
        "details": results
    }
