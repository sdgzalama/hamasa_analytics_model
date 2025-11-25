import time
from database.connection import get_db
from scrapers.rss_scraper import scrape_rss
from scrapers.web_scraper import scrape_webpage
from utils.logs import log_scrape

SCRAPE_INTERVAL = 300  # 5 minutes
last_index = 0


def scraper_scheduler():
    global last_index

    while True:
        try:
            # Load all media sources
            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, name, base_url
                FROM media_sources
                WHERE base_url IS NOT NULL AND base_url != ''
                ORDER BY name ASC
            """)
            sources = cursor.fetchall()
            cursor.close()
            conn.close()

            if not sources:
                print("[SCRAPER] No media sources found")
                time.sleep(SCRAPE_INTERVAL)
                continue

            if last_index >= len(sources):
                last_index = 0

            src = sources[last_index]
            source_id = src["id"]
            base_url = src["base_url"]
            source_name = src["name"]

            print(f"[SCRAPER] ({last_index+1}/{len(sources)}) Scraping {source_name}")

            conn = get_db()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT project_id
                FROM project_media_sources
                WHERE media_source_id=%s
            """, (source_id,))
            projects = cursor.fetchall()
            cursor.close()
            conn.close()

            for p in projects:
                pid = p["project_id"]

                if "rss" in base_url or base_url.endswith(".xml"):
                    scrape_rss(pid, source_id, base_url)
                else:
                    scrape_webpage(pid, source_id)

            last_index += 1

        except Exception as e:
            print("[SCRAPER ERROR]", e)
            log_scrape(
                source_id="scheduler",
                source_name="scraper_scheduler",
                project_id=None,
                method="system",
                new_items=0,
                reused_items=0,
                status="error",
                message=str(e)
            )

        time.sleep(SCRAPE_INTERVAL)
