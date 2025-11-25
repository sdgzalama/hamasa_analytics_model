from database.connection import get_db

def load_project_details(project_id: str):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    project = {}

    # 1. Load main project row
    cursor.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
    base = cursor.fetchone()

    if not base:
        cursor.close()
        conn.close()
        raise Exception("Project not found")

    project.update(base)

    # 2. Load media_source_ids from mapping table
    cursor.execute("""
        SELECT media_source_id
        FROM project_media_sources
        WHERE project_id = %s
    """, (project_id,))
    source_id_rows = cursor.fetchall()

    source_ids = [row["media_source_id"] for row in source_id_rows]

    # 3. Load actual media sources
    if source_ids:
        placeholders = ",".join(["%s"] * len(source_ids))
        query = f"""
            SELECT *
            FROM media_sources
            WHERE id IN ({placeholders})
        """
        cursor.execute(query, tuple(source_ids))
        project["media_sources"] = cursor.fetchall()
    else:
        project["media_sources"] = []

    # 4. Load project thematic areas
    cursor.execute("""
        SELECT *
        FROM thematic_areas
        WHERE project_id = %s
    """, (project_id,))
    project["thematic_areas"] = cursor.fetchall()

    cursor.close()
    conn.close()

    return project
