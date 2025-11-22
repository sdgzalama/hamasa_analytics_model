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
