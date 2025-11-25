import uuid
from database.connection import get_db

def log_scrape(source_id, source_name, project_id, method, new_items, reused_items, status, message=""):
    """Write scraping activity into scrape_logs table."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scrape_logs(
                id, timestamp, source_id, source_name, project_id,
                method, new_items, reused_items, status, message
            )
            VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            str(uuid.uuid4()),
            source_id,
            source_name,
            project_id,
            method,
            new_items,
            reused_items,
            status,
            message
        ))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("[SCRAPE LOGGING ERROR]", e)
