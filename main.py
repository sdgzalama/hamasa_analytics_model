from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database.connection import get_db
import threading
import os


# SCHEDULERS
from schedulers.sync_scheduler import start_sync_scheduler
from worker.scheduler import start_scheduler            # AI analysis scheduler
from schedulers.scraper_scheduler import scraper_scheduler   # Web/RSS scraper scheduler

# ROUTERS

from routers.project_insights import router as project_insights_router
from routers import (
    health,
    projects,
    items,
    test_db,
    clients,
    scrape,
    analysis,
    dashboard,
    project_dashboard,
    media_sources,
    project_media,
    thematic_area,
    project_reports,
    project_setup
)

# ------------------------------------
# START SCRAPER SCHEDULER ON BOOT
# ------------------------------------
threading.Thread(target=scraper_scheduler, daemon=True).start()

load_dotenv()

app = FastAPI(
    title="Media Monitoring Backend",
    version="1.0.0",
    description="AI-powered media monitoring system"
)

# ------------------------------------
# STARTUP EVENTS
# ------------------------------------
@app.on_event("startup")
def startup_event():
    # Start AI scheduler (runs every X mins)
    start_scheduler()
    start_sync_scheduler()  # Start sync scheduler (runs every 6 hours)

    # DB health check
    try:
        conn = get_db()
        conn.close()
        print("[STARTUP] Database connection OK")
    except Exception as e:
        print("[STARTUP ERROR] Database not available:", e)


# ------------------------------------
# ROOT ENDPOINT
# ------------------------------------
@app.get("/")
async def root():
    return {
        "message": "Media Monitoring Backend is running.",
        "docs": "Visit /docs to explore API documentation."
    }


# ------------------------------------
# CORS CONFIG
# ------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------
# ROUTE REGISTRATION
# ------------------------------------
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(clients.router)
app.include_router(items.router)
app.include_router(scrape.router)
app.include_router(analysis.router)
app.include_router(dashboard.router)
app.include_router(project_dashboard.router)
app.include_router(media_sources.router)
app.include_router(project_insights_router)
app.include_router(project_media.router)
app.include_router(thematic_area.router)
app.include_router(project_reports.router)
app.include_router(project_setup.router)

# uvicorn.run is removed — Render/your host manages the server
