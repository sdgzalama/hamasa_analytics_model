from fastapi import APIRouter
from database.connection import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Total projects
    cursor.execute("SELECT COUNT(*) AS total FROM projects")
    total_projects = cursor.fetchone()["total"]

    # Total media items
    cursor.execute("SELECT COUNT(*) AS total FROM media_items")
    total_items = cursor.fetchone()["total"]

    # Awaiting AI Processing
    cursor.execute("SELECT COUNT(*) AS total FROM media_items WHERE analysis_status = 'raw'")
    awaiting = cursor.fetchone()["total"]

    # Completed extractions
    cursor.execute("SELECT COUNT(*) AS total FROM media_items WHERE analysis_status = 'extracted'")
    completed = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return {
        "total_projects": total_projects,
        "total_items": total_items,
        "awaiting": awaiting,
        "completed": completed
    }

