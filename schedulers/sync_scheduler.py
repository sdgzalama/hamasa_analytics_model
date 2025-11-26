import time
import requests
import os
from fastapi import HTTPException
from database.connection import get_db
import threading
import json

HAMASA_API = os.getenv("HAMASA_API_URL", "http://13.48.124.122/hamasa-api/v1")
API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MjRmNTQwMi01NjAyLTRjYmYtODA0ZS0wOGUyNzFmZDAwM2MiLCJyb2xlIjoib3JnX3VzZXIiLCJlbWFpbCI6InNpZGFnYXdhemlyaWtpaG9uZ29AZ21haWwuY29tIiwiZXhwIjoxNzY0MDk2MjE3fQ.mNPNCui3vQoDDC-xwsEk7ELuOpYCI8y4johYJle2raw"

SYNC_INTERVAL = 60 * 60 * 2   #every 2 hours


def fetch_all_projects():
    """Pull full project list from Hamasa API."""
    url = f"{HAMASA_API}/projects/"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}"
    }

    print("[SYNC] Fetching project list from Hamasa...")
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        print("[SYNC ERROR] Cannot load projects:", r.text)
        return []

    data = r.json()
    return data.get("results", [])


def import_project(project):
    """Insert or update project + client + media sources into DB."""

    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        project_id = project["id"]
        title = project["title"]
        description = project["description"]
        client_id = project["client_id"]

        # 🟢 UPSERT PROJECT
        cursor.execute("SELECT id FROM projects WHERE id=%s", (project_id,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO projects(id, client_id, title, description)
                VALUES (%s, %s, %s, %s)
            """, (project_id, client_id, title, description))
        else:
            cursor.execute("""
                UPDATE projects SET client_id=%s, title=%s, description=%s
                WHERE id=%s
            """, (client_id, title, description, project_id))

        # 🟢 UPSERT MEDIA SOURCES
        for src in project.get("media_sources", []):
            src_id = src["id"]
            name = src["name"]
            category = src.get("category_name", "")

            cursor.execute("SELECT id FROM media_sources WHERE id=%s", (src_id,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("""
                    INSERT INTO media_sources(id, name, type)
                    VALUES (%s, %s, %s)
                """, (src_id, name, category))
            else:
                cursor.execute("""
                    UPDATE media_sources SET name=%s, type=%s WHERE id=%s
                """, (name, category, src_id))

            cursor.execute("""
                INSERT IGNORE INTO project_media_sources(project_id, media_source_id)
                VALUES (%s, %s)
            """, (project_id, src_id))

        # 🟢 UPSERT THEMATIC AREAS
        for t in project.get("thematic_areas", []):
            thematic_id = t["id"]
            cursor.execute("SELECT id FROM thematic_areas WHERE id=%s", (thematic_id,))
            exists = cursor.fetchone()

            cursor.execute("""
                INSERT INTO thematic_areas(id, project_id, name, description, monitoring_objectives)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    description=VALUES(description),
                    monitoring_objectives=VALUES(monitoring_objectives)
            """, (
                thematic_id,
                project_id,
                t["title"],
                t["description"],
                json.dumps(t.get("monitoring_objectives", []))
            ))

        conn.commit()
        print(f"[SYNC] Project imported: {project_id}")

    except Exception as e:
        conn.rollback()
        print("[SYNC ERROR] Failed to import:", e)

    finally:
        cursor.close()
        conn.close()


def sync_loop():
    """MAIN SYNC LOOP (runs forever)"""
    while True:
        projects = fetch_all_projects()

        for p in projects:
            import_project(p)

        print("[SYNC] Completed. Next sync in 6 hours.")
        time.sleep(SYNC_INTERVAL)


def start_sync_scheduler():
    """Start sync loop as background thread."""
    thread = threading.Thread(target=sync_loop, daemon=True)
    thread.start()
    print("[SYNC] Auto-sync scheduler started.")
