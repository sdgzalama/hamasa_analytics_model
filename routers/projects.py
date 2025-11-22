# backend/routers/projects.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database.connection import get_db
import uuid
from nlp.semantic_generator import generate_semantic_areas

router = APIRouter(prefix="/projects", tags=["Projects"])


# ----------------------------------
# Pydantic Data Model
# ----------------------------------
class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None
    client_id: str

    category_ids: List[str] = []
    collaborator_ids: List[str] = []
    media_source_ids: List[str] = []
    report_avenue_ids: List[str] = []
    report_time_ids: List[str] = []
    report_consultation_ids: List[str] = []


# ----------------------------------
# POST: Create Project
# ----------------------------------
@router.post("/")
def create_project(project: ProjectCreate):

    project_id = str(uuid.uuid4())

    try:
        conn = get_db()
        cursor = conn.cursor()

        # ----------------------------
        # 1. Insert into main project table
        # ----------------------------
        insert_project_sql = """
            INSERT INTO projects (id, title, description, client_id)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_project_sql, (
            project_id,
            project.title,
            project.description,
            project.client_id
        ))

        # ----------------------------
        # 2. Helper for many-to-many mappings
        # ----------------------------
        def insert_many(table, items, column_name):
            if items:
                sql = f"INSERT INTO {table} (project_id, {column_name}) VALUES (%s, %s)"
                cursor.executemany(sql, [(project_id, item) for item in items])

        insert_many("project_categories", project.category_ids, "category_id")
        insert_many("project_collaborators", project.collaborator_ids, "collaborator_id")
        insert_many("project_media_sources", project.media_source_ids, "media_source_id")
        insert_many("project_report_avenues", project.report_avenue_ids, "report_avenue_id")
        insert_many("project_report_times", project.report_time_ids, "report_time_id")
        insert_many("project_report_consultations", project.report_consultation_ids, "report_consultation_id")

        conn.commit()

        # ----------------------------
        # 3. Generate AI Semantic Areas
        # ----------------------------
        semantic_areas = generate_semantic_areas(
            project_id=project_id,
            title=project.title,
            description=project.description or ""
        )

        # ----------------------------
        # 4. Final Response
        # ----------------------------
        return {
            "status": "success",
            "message": "Project created successfully",
            "data": {
                "id": project_id,
                "title": project.title,
                "description": project.description,
                "client_id": project.client_id,
                "category_ids": project.category_ids,
                "collaborator_ids": project.collaborator_ids,
                "media_source_ids": project.media_source_ids,
                "report_time_ids": project.report_time_ids,
                "report_avenue_ids": project.report_avenue_ids,
                "report_consultation_ids": project.report_consultation_ids,
            },
            "thematic_areas": semantic_areas
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {str(e)}"
        )

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

# ----------------------------------
# GET: List all projects
# ----------------------------------
# ----------------------------------
# GET: List all projects + thematic areas
# ----------------------------------
# ----------------------------------
# GET: List all projects + thematic areas + media sources
# ----------------------------------
@router.get("/")
def list_projects():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # 1. Fetch base project info
    cursor.execute("""
        SELECT 
            p.id,
            p.title AS name,
            p.description,
            c.name AS client_name
        FROM projects p
        LEFT JOIN clients c ON p.client_id = c.id
        ORDER BY p.created_at DESC
    """)

    projects = cursor.fetchall()

    # 2. Attach thematic areas + project-specific media sources
    for p in projects:

        # -----------------------------
        # THEMATIC AREAS
        # -----------------------------
        cursor.execute("""
            SELECT name 
            FROM thematic_areas
            WHERE project_id = %s
        """, (p["id"],))
        themes = cursor.fetchall()
        p["thematic_areas"] = [t["name"] for t in themes]

        # -----------------------------
        # MEDIA SOURCES (only for this project)
        # -----------------------------
        # -----------------------------
# MEDIA SOURCES (only for this project)
# -----------------------------
        cursor.execute("""
            SELECT 
                ms.id,
                ms.name,
                ms.base_url,
                ms.type
            FROM media_sources ms
            JOIN project_media_sources pms ON pms.media_source_id = ms.id
            WHERE pms.project_id = %s
            ORDER BY ms.name ASC
        """, (p["id"],))


        sources = cursor.fetchall()
        p["media_sources"] = sources

    cursor.close()
    conn.close()

    return projects
