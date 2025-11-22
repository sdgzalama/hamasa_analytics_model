from fastapi import APIRouter, HTTPException
from database.connection import get_db
from uuid import uuid4

router = APIRouter(prefix="/project", tags=["Thematic Areas"])


# ------------------------------------------------------------
# GET ALL THEMATIC AREAS FOR A PROJECT
# ------------------------------------------------------------
@router.get("/{project_id}/thematics")
def get_thematics(project_id: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()

    if not project:
        cursor.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    cursor.execute("""
        SELECT id, name, description, created_at
        FROM thematic_areas
        WHERE project_id = %s
        ORDER BY created_at DESC
    """, (project_id,))

    areas = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"project": project, "thematic_areas": areas}


# ------------------------------------------------------------
# CREATE NEW THEMATIC AREA
# ------------------------------------------------------------
@router.post("/{project_id}/thematics")
def create_thematic_area(project_id: str, body: dict):

    name = body.get("name")
    description = body.get("description") or ""

    if not name:
        raise HTTPException(status_code=400, detail="Theme name is required")

    conn = get_db()
    cursor = conn.cursor()

    theme_id = str(uuid4())

    cursor.execute("""
        INSERT INTO thematic_areas (id, project_id, name, description)
        VALUES (%s, %s, %s, %s)
    """, (theme_id, project_id, name, description))

    conn.commit()
    cursor.close()
    conn.close()

    return {"id": theme_id, "name": name, "description": description}


# ------------------------------------------------------------
# DELETE THEMATIC AREA
# ------------------------------------------------------------
@router.delete("/thematic/{thematic_id}")
def delete_thematic_area(thematic_id: str):

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM thematic_areas WHERE id = %s", (thematic_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return {"status": "deleted", "id": thematic_id}
