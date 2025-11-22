from fastapi import APIRouter
from database.connection import get_db
from fastapi import HTTPException

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_stats():

    conn = None
    cursor = None

    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total FROM projects")
        total_projects = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM media_items")
        total_items = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM media_items WHERE analysis_status = 'raw'")
        awaiting = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM media_items WHERE analysis_status = 'extracted'")
        completed = cursor.fetchone()["total"]

        return {
            "total_projects": total_projects,
            "total_items": total_items,
            "awaiting": awaiting,
            "completed": completed
        }

    except Exception as e:
        print("DASHBOARD ERROR:", e)
        raise HTTPException(status_code=500, detail="Failed to load dashboard stats")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
