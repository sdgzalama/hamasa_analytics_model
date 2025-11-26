import time
import requests
import json
import threading
from database.connection import get_db

BASE_URL = "http://13.48.124.122/hamasa-api/v1"

IDENTIFIER = "0746424480"
PASSWORD = "12345678"

SYNC_INTERVAL = 60 * 60 * 6   # 6 hours


# ----------------------------------------------------------
# 1️⃣ LOGIN – ALWAYS RUN FIRST
# ----------------------------------------------------------
def login():
    url = f"{BASE_URL}/auth/login"

    payload = {
        "identifier": IDENTIFIER,
        "password": PASSWORD
    }

    print("[SYNC LOGIN] Logging into Hamasa...")
    r = requests.post(url, json=payload)

    print("[SYNC LOGIN STATUS]:", r.status_code)
    print("[SYNC LOGIN RESPONSE]:", r.text)

    if r.status_code != 200:
        print("[SYNC LOGIN ERROR] Login failed.")
        return None

    token = r.json().get("access_token")
    print("[SYNC LOGIN] Token received.")
    return token


# ----------------------------------------------------------
# 2️⃣ GET PROJECTS USING TOKEN
# ----------------------------------------------------------
def fetch_projects(token):
    all_results = []
    page = 1

    while True:
        url = f"{BASE_URL}/projects/projects_ml/?page={page}&page_size=100&sort=desc"
        headers = {"Authorization": f"Bearer {token}"}

        print(f"[SYNC] Fetching projects page {page}…")
        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            print("[SYNC ERROR] Cannot load projects:", r.text)
            break

        data = r.json()
        results = data.get("results", [])

        if not results:
            break  # no more pages

        all_results.extend(results)

        if data.get("next") is None:
            break  # finished

        page += 1

    return all_results



# ----------------------------------------------------------
# 3️⃣ SAVE PROJECT TO YOUR DB
# ----------------------------------------------------------
def upsert_project(p):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        pid = p["id"]
        title = p["title"]
        description = p.get("description", "")
        client_id = p["client_id"]

        # ----------------------------------------------------------
        # 1️⃣ UPSERT CLIENT FIRST (required because of FK)
        # ----------------------------------------------------------
        cursor.execute("SELECT id FROM clients WHERE id=%s", (client_id,))
        exists = cursor.fetchone()

        # Hamasa API does NOT return client details → use placeholder name
        placeholder_name = f"Client-{client_id[:6]}"

        if not exists:
            cursor.execute("""
                INSERT INTO clients(id, name)
                VALUES (%s, %s)
            """, (client_id, placeholder_name))
        else:
            cursor.execute("""
                UPDATE clients SET name=%s WHERE id=%s
            """, (placeholder_name, client_id))

        # ----------------------------------------------------------
        # 2️⃣ UPSERT PROJECT
        # ----------------------------------------------------------
        cursor.execute("SELECT id FROM projects WHERE id=%s", (pid,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO projects(id, client_id, title, description)
                VALUES (%s, %s, %s, %s)
            """, (pid, client_id, title, description))
        else:
            cursor.execute("""
                UPDATE projects SET client_id=%s, title=%s, description=%s
                WHERE id=%s
            """, (client_id, title, description, pid))

        # ----------------------------------------------------------
        # 3️⃣ UPSERT MEDIA SOURCES
        # ----------------------------------------------------------
        for src in p.get("media_sources", []):
            sid = src["id"]
            name = src["name"]
            category = src.get("category_name", "")

            cursor.execute("SELECT id FROM media_sources WHERE id=%s", (sid,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("""
                    INSERT INTO media_sources(id, name, type)
                    VALUES (%s, %s, %s)
                """, (sid, name, category))
            else:
                cursor.execute("""
                    UPDATE media_sources SET name=%s, type=%s WHERE id=%s
                """, (name, category, sid))

            cursor.execute("""
                INSERT IGNORE INTO project_media_sources(project_id, media_source_id)
                VALUES (%s, %s)
            """, (pid, sid))

        # ----------------------------------------------------------
        # 4️⃣ UPSERT THEMATIC AREAS
        # ----------------------------------------------------------
        for t in p.get("thematic_areas", []):
            tid = t["id"]

            cursor.execute("""
                INSERT INTO thematic_areas(id, project_id, name, description, monitoring_objectives)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name=VALUES(name),
                    description=VALUES(description),
                    monitoring_objectives=VALUES(monitoring_objectives)
            """, (
                tid, pid,
                t["title"],
                t["description"],
                json.dumps(t.get("monitoring_objectives", []))
            ))

        conn.commit()
        print(f"[SYNC] Imported project: {pid}")

    except Exception as e:
        conn.rollback()
        print("[SYNC ERROR] Failed to import project:", e)

    finally:
        cursor.close()
        conn.close()



# ----------------------------------------------------------
# 4️⃣ MAIN LOOP
# ----------------------------------------------------------
def sync_loop():
    while True:
        print("[SYNC] Starting new sync cycle...")

        # LOGIN FIRST
        token = login()
        if not token:
            print("[SYNC] Login failed. Retrying next cycle...")
            time.sleep(SYNC_INTERVAL)
            continue

        # FETCH PROJECTS WITH FRESH TOKEN
        projects = fetch_projects(token)

        for p in projects:
            upsert_project(p)

        print("[SYNC] Completed. Next sync in 6 hours.")
        time.sleep(SYNC_INTERVAL)


# ----------------------------------------------------------
# 5️⃣ START BACKGROUND THREAD
# ----------------------------------------------------------
def start_sync_scheduler():
    def delayed_start():
        time.sleep(5)  # slight delay to ensure DB is ready
        sync_loop()
    thread = threading.Thread(target=sync_loop, daemon=True)
    thread.start()
    print("[SYNC] Auto-sync scheduler started.")
