from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os
import uuid
from database.connection import get_db

router = APIRouter(prefix="/import", tags=["Project Import"])

HAMASA_API = "http://13.48.124.122/hamasa-api/v1/projects"
HAMASA_TOKEN ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4MjRmNTQwMi01NjAyLTRjYmYtODA0ZS0wOGUyNzFmZDAwM2MiLCJyb2xlIjoib3JnX3VzZXIiLCJlbWFpbCI6InNpZGFnYXdhemlyaWtpaG9uZ29AZ21haWwuY29tIiwiZXhwIjoxNzY0MDk2MjE3fQ.mNPNCui3vQoDDC-xwsEk7ELuOpYCI8y4johYJle2raw" # store token in environment


class ImportRequest(BaseModel):
    project_id: str


@router.post("/project")
def import_project(data: ImportRequest):

    if not HAMASA_TOKEN:
        raise HTTPException(500, "Missing HAMASA_API_TOKEN env variable")

    # -------------------------------
    # 1️⃣ Fetch project from main API
    # -------------------------------
    url = f"{HAMASA_API}/{data.project_id}"
    headers = {"Authorization": f"Bearer {HAMASA_TOKEN}"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise HTTPException(response.status_code, "Failed to fetch project from Hamasa API")

    project_data = response.json()

    # ------------------------------------
    # 2️⃣ Parse fields from Hamasa response
    # ------------------------------------
    project_id = project_data["id"]
    title = project_data["title"]
    description = project_data["description"]
    client_id = project_data["client_id"]

    media_sources = project_data.get("media_sources", [])
    thematic_areas = project_data.get("thematic_areas", [])
    report_avenues = project_data.get("report_avenues", [])
    report_times = project_data.get("report_times", [])
    report_consultations = project_data.get("report_consultations", [])

    # -----------------------------
    # 3️⃣ Insert into your database
    # -----------------------------
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # 🔹 UPSERT CLIENT
    cursor.execute("SELECT id FROM clients WHERE id=%s", (client_id,))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("""
            INSERT INTO clients(id, name)
            VALUES (%s, %s)
        """, (client_id, project_data["title"]))   # no client name available in API?
    else:
        cursor.execute("""
            UPDATE clients SET name=%s WHERE id=%s
        """, (project_data["title"], client_id))

    # 🔹 UPSERT PROJECT
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

    # 🔹 UPSERT MEDIA SOURCES
    for src in media_sources:
        name = src["name"]
        category = src.get("category_name", "")
        source_id = src["id"]

        cursor.execute("SELECT id FROM media_sources WHERE id=%s", (source_id,))
        exists = cursor.fetchone()

        if not exists:
            cursor.execute("""
                INSERT INTO media_sources(id, name, type)
                VALUES (%s, %s, %s)
            """, (source_id, name, category))
        else:
            cursor.execute("""
                UPDATE media_sources SET name=%s, type=%s
                WHERE id=%s
            """, (name, category, source_id))

        cursor.execute("""
            INSERT IGNORE INTO project_media_sources(project_id, media_source_id)
            VALUES (%s, %s)
        """, (project_id, source_id))

    # 🔹 UPSERT THEMATIC AREAS
    import json
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
                thematic_id, project_id,
                t["title"], t["description"], monitoring_json
            ))
        else:
            cursor.execute("""
                UPDATE thematic_areas
                SET name=%s, description=%s, monitoring_objectives=%s
                WHERE id=%s
            """, (
                t["title"], t["description"], monitoring_json, thematic_id
            ))

    conn.commit()
    cursor.close()
    # conn.close()

    return {
        "status": "success",
        "message": "Project imported successfully",
        "project_id": project_id
    }
