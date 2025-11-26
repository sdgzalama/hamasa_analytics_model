from fastapi import APIRouter
from worker.sync_projects import login, fetch_projects, upsert_project

router = APIRouter(prefix="/sync", tags=["Project Sync"])


@router.get("/projects")
def sync_now():
    """Manually trigger project sync."""

    # 🔥 ALWAYS LOGIN FIRST
    token = login()
    if not token:
        return {"status": "error", "message": "Login failed"}

    # 🔥 Get projects using the token
    projects = fetch_projects(token)

    imported = 0
    for p in projects:
        upsert_project(p)
        imported += 1

    return {
        "status": "ok",
        "imported": imported,
        "count": len(projects)
    }
