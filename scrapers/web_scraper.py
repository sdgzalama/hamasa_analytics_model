import uuid
import requests
from bs4 import BeautifulSoup
from readability import Document
from database.connection import get_db
from datetime import datetime
from utils.logs import log_scrape


def extract_clean_text(html: str):
    """Extract readable text using Readability with fallback."""
    try:
        doc = Document(html)
        cleaned_html = doc.summary()

        soup = BeautifulSoup(cleaned_html, "html.parser")
        paragraphs = soup.find_all(["p", "h1", "h2", "h3"])

        text = "\n".join(p.get_text(strip=True) for p in paragraphs)
        return text.strip()

    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text(strip=True) for p in paragraphs).strip()


def scrape_webpage(project_id: str, source_id: str):
    """Scrape normal websites (non-RSS)."""

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name, base_url FROM media_sources WHERE id=%s", (source_id,))
    row = cursor.fetchone()

    if not row or not row["base_url"]:
        return {"new_items": 0, "reused_items": 0, "items": []}

    base_url = row["base_url"]
    source_name = row["name"]

    print("Web Scraper: Fetching", base_url)

    try:
        response = requests.get(base_url, timeout=12, headers={
            "User-Agent": "Mozilla/5.0"
        })
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract all possible article links
        links = []
        for a in soup.find_all("a"):
            href = a.get("href")
            title = a.get_text(strip=True)

            if not href or not title:
                continue

            if href.startswith("#"):
                continue

            if href.startswith("/"):
                href = base_url.rstrip("/") + href

            links.append((title, href))

        links = links[:10]  # safety limit

        new_items = 0
        reused_items = 0
        results = []

        for title, url in links:
            cursor.execute("SELECT id FROM media_items WHERE url=%s LIMIT 1", (url,))
            existing = cursor.fetchone()

            if existing:
                media_id = existing["id"]
                reused_items += 1
            else:
                try:
                    article_resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
                    article_html = article_resp.text
                    clean_text = extract_clean_text(article_html)
                except Exception:
                    clean_text = ""

                media_id = str(uuid.uuid4())

                cursor.execute("""
                    INSERT INTO media_items(id, source_id, raw_title, raw_text, url, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    media_id,
                    source_id,
                    title,
                    clean_text,
                    url,
                    datetime.now()
                ))
                new_items += 1

            cursor.execute("""
                INSERT IGNORE INTO project_media_items(project_id, media_item_id)
                VALUES (%s, %s)
            """, (project_id, media_id))

            results.append({
                "media_id": media_id,
                "title": title,
                "url": url
            })

        conn.commit()
        cursor.close()
        conn.close()

        log_scrape(
            source_id=source_id,
            source_name=source_name,
            project_id=project_id,
            method="web",
            new_items=new_items,
            reused_items=reused_items,
            status="success",
            message="Web scraping complete"
        )

        return {
            "new_items": new_items,
            "reused_items": reused_items,
            "items": results
        }

    except Exception as e:
        log_scrape(
            source_id=source_id,
            source_name=source_name,
            project_id=project_id,
            method="web",
            new_items=0,
            reused_items=0,
            status="error",
            message=str(e)
        )
        return {"error": str(e)}
