import uuid
import feedparser
import requests
from bs4 import BeautifulSoup
from database.connection import get_db
from datetime import datetime


# ---------------------------------------------------------
# FETCH FULL ARTICLE TEXT
# ---------------------------------------------------------
def fetch_article_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join([p.get_text(strip=True) for p in paragraphs]).strip()
    except Exception as e:
        print("Article fetch failed:", e)
        return ""


# ---------------------------------------------------------
# CHECK IF URL ALREADY EXISTS
# ---------------------------------------------------------
def get_existing_item_id(url: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM media_items WHERE url = %s LIMIT 1", (url,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else None


# ---------------------------------------------------------
# SAVE NEW MEDIA ITEM
# ---------------------------------------------------------
def save_media_item(source_id, title, text, url, published_at):
    conn = get_db()
    cursor = conn.cursor()
    media_id = str(uuid.uuid4())

    cursor.execute("""
        INSERT INTO media_items (
            id, source_id, raw_title, raw_text, url, published_at
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, (media_id, source_id, title, text, url, published_at))

    conn.commit()
    cursor.close()
    conn.close()

    return media_id


# ---------------------------------------------------------
# LINK ITEM TO PROJECT
# ---------------------------------------------------------
def link_item_to_project(project_id, media_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT IGNORE INTO project_media_items (project_id, media_item_id)
        VALUES (%s, %s)
    """, (project_id, media_id))

    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------------------------------------
# MAIN SCRAPER — CLEAN VERSION (NO AI)
# ---------------------------------------------------------
def scrape_rss(project_id: str, source_id: str, feed_url: str):
    print("Scraping RSS:", feed_url)

    feed = feedparser.parse(feed_url)
    if not feed.entries:
        return {"new_items": 0, "reused_items": 0, "items": []}

    # ----------------------------------------------------
    # GET ALL PROJECTS USING THIS SOURCE
    # ----------------------------------------------------
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT project_id
        FROM project_media_sources
        WHERE media_source_id = %s
    """, (source_id,))

    all_projects = cursor.fetchall()
    project_ids = [p["project_id"] for p in all_projects]

    cursor.close()
    conn.close()

    print("Source shared to these projects:", project_ids)

    inserted = 0
    reused = 0
    results = []

    # ----------------------------------------------------
    # PROCESS FEED ITEMS
    # ----------------------------------------------------
    for entry in feed.entries:
        title = entry.get("title", "")
        url = entry.get("link", "")
        if not url:
            continue

        published = None
        if entry.get("published_parsed"):
            published = datetime(*entry.published_parsed[:6])

        # Check if item already exists
        existing_id = get_existing_item_id(url)

        if existing_id:
            for pid in project_ids:
                link_item_to_project(pid, existing_id)
            reused += 1
            continue

        # Save new item
        text = fetch_article_text(url)
        media_id = save_media_item(source_id, title, text, url, published)

        for pid in project_ids:
            link_item_to_project(pid, media_id)

        inserted += 1
        results.append({
            "media_id": media_id,
            "title": title,
            "url": url,
            "published_at": published
        })

    # ----------------------------------------------------
    # IMPORTANT!! — NO AI CALLS HERE
    # ----------------------------------------------------

    return {
        "new_items": inserted,
        "reused_items": reused,
        "items": results
    } 
