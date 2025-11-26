from fastapi import APIRouter, HTTPException
from database.connection import get_db
import json
import uuid

from scrapers.rss_scraper import scrape_rss
from scrapers.web_scraper import scrape_webpage   # <-- you must create this file

router = APIRouter(prefix="/setup", tags=["Project Setup"])


@router.post("/project")
def setup_project(project_data: dict):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    try:
        project_id = project_data["id"]
        client = project_data["client"]
        media_sources = project_data.get("media_sources", [])
        thematic_areas = project_data.get("thematic_areas", [])
        report_avenues = project_data.get("report_avenues", [])
        report_times = project_data.get("report_times", [])
        report_consultations = project_data.get("report_consultations", [])

        # -------------------------------------
        # 1. UPSERT CLIENT
        # -------------------------------------
        cursor.execute("SELECT id FROM clients WHERE id=%s", (client["id"],))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO clients(id, name, contact_email)
                VALUES (%s, %s, %s)
            """, (client["id"], client["name_of_organisation"], client["email"]))
        else:
            cursor.execute("""
                UPDATE clients
                SET name=%s, contact_email=%s
                WHERE id=%s
            """, (client["name_of_organisation"], client["email"], client["id"]))

        # -------------------------------------
        # 2. UPSERT PROJECT
        # -------------------------------------
        cursor.execute("SELECT id FROM projects WHERE id=%s", (project_id,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO projects(id, client_id, title, description)
                VALUES (%s, %s, %s, %s)
            """, (project_id, client["id"], project_data["title"], project_data["description"]))
        else:
            cursor.execute("""
                UPDATE projects
                SET client_id=%s, title=%s, description=%s
                WHERE id=%s
            """, (client["id"], project_data["title"], project_data["description"], project_id))

        # -------------------------------------
        # 3. BEST PRACTICE: UPSERT MEDIA SOURCES BY NAME ONLY
        # -------------------------------------
        new_project_sources = []  # store source_ids linked to this project

        for src in media_sources:
            src_name = src["name"].strip()

            # match by NAME
            cursor.execute("""
                SELECT id FROM media_sources
                WHERE name = %s
                LIMIT 1
            """, (src_name,))
            existing = cursor.fetchone()

            if existing:
                source_id = existing["id"]
                cursor.execute("UPDATE media_sources SET type=%s WHERE id=%s",
                               (src["category_name"], source_id))
            else:
                source_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO media_sources(id, name, type)
                    VALUES (%s, %s, %s)
                """, (source_id, src_name, src["category_name"]))

            # map to project
            cursor.execute("""
                INSERT IGNORE INTO project_media_sources(project_id, media_source_id)
                VALUES (%s, %s)
            """, (project_id, source_id))

            new_project_sources.append(source_id)

        # -------------------------------------
        # 4. UPSERT THEMATIC AREAS
        # -------------------------------------
        for t in thematic_areas:
            thematic_id = t["id"]
            monitoring_json = json.dumps(t.get("monitoring_objectives", []))

            cursor.execute("SELECT id FROM thematic_areas WHERE id=%s", (thematic_id,))
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("""
                    INSERT INTO thematic_areas(id, project_id, name, description, monitoring_objectives)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    thematic_id,
                    project_id,
                    t["title"],
                    t["description"],
                    monitoring_json
                ))
            else:
                cursor.execute("""
                    UPDATE thematic_areas
                    SET name=%s, description=%s, monitoring_objectives=%s
                    WHERE id=%s
                """, (
                    t["title"],
                    t["description"],
                    monitoring_json,
                    thematic_id
                ))

        # -------------------------------------
        # SAVE EVERYTHING BEFORE SCRAPING
        # -------------------------------------
        conn.commit()

        # -------------------------------------
        # 5. AUTO-SCRAPE ALL SOURCES FOR THIS PROJECT
        # -------------------------------------
        scrape_results = []

        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, base_url
            FROM media_sources
            WHERE id IN (
                SELECT media_source_id FROM project_media_sources WHERE project_id = %s
            )
        """, (project_id,))

        sources = cursor.fetchall()

        for s in sources:
            src_id = s["id"]
            base_url = s["base_url"]

            # RSS scraping
            if base_url and (base_url.endswith(".xml") or "rss" in base_url.lower()):
                result = scrape_rss(project_id, src_id, base_url)
                scrape_results.append({"source": s["name"], "method": "rss", "result": result})

            # Web scraping fallback
            elif base_url:
                result = scrape_webpage(project_id, src_id)
                scrape_results.append({"source": s["name"], "method": "web", "result": result})

            else:
                scrape_results.append({"source": s["name"], "method": "none", "reason": "No base_url"})


        return {
            "status": "success",
            "project_id": project_id,
            "scraping": scrape_results
        }

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        # conn.close()
