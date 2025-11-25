import uuid
import feedparser
import requests
from bs4 import BeautifulSoup
from database.connection import get_db
from datetime import datetime
from utils.logs import log_scrape


# ---------------------------------------------------------
# FETCH FULL ARTICLE TEXT (simple + readability fallback)
# ---------------------------------------------------------
def fetch_article_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        html = response.text

        # 1) Try readability cleaner
        try:
            from readability import Document
            doc = Document(html)
            cleaned_html = doc.summary()
            soup = BeautifulSoup(cleaned_html, "html.parser")
            paragraphs = soup.find_all(["p", "h1", "h2"])
            text = "\n".join([p.get_text(strip=True) for p in paragraphs])
            if len(text) > 50:
                return text
        except:
            pass

        # 2) Fallback simple extraction
        soup = BeautifulSoup(html, "html.parser")
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
    cursor.execute("SELECT id FROM media_items WHERE url=%s LIMIT 1", (url,))
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
# MAIN RSS SCRAPER
# ---------------------------------------------------------
def scrape_rss(project_id: str, source_id: str, feed_url: str):
    print("Scraping RSS:", feed_url)

    try:
        feed = feedparser.parse(feed_url)
        if not feed.entries:
            return {"new_items": 0, "reused_items": 0, "items": []}

        # Load all linked projects
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT project_id
            FROM project_media_sources
            WHERE media_source_id=%s
        """, (source_id,))
        project_ids = [p["project_id"] for p in cursor.fetchall()]
        cursor.close()
        conn.close()

        inserted = 0
        reused = 0
        results = []

        for entry in feed.entries:
            title = entry.get("title", "")
            url = entry.get("link", "")
            if not url:
                continue

            published = None
            if entry.get("published_parsed"):
                published = datetime(*entry.published_parsed[:6])

            existing = get_existing_item_id(url)

            # Already in DB? Link only.
            if existing:
                for pid in project_ids:
                    link_item_to_project(pid, existing)
                reused += 1
                continue

            # Fetch missing article text
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

        # --- LOG SUCCESS ---
        log_scrape(
            source_id=source_id,
            source_name=feed_url,
            project_id=project_id,
            method="rss",
            new_items=inserted,
            reused_items=reused,
            status="success",
            message="RSS scrape completed"
        )

        return {
            "new_items": inserted,
            "reused_items": reused,
            "items": results
        }

    except Exception as e:
        # --- LOG ERROR (missing in your version) ---
        log_scrape(
            source_id=source_id,
            source_name=feed_url,
            project_id=project_id,
            method="rss",
            new_items=0,
            reused_items=0,
            status="error",
            message=str(e)
        )
        print("[RSS SCRAPER ERROR]:", e)
        return {"error": str(e)}
