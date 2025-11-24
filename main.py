from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database.connection import get_db
import os


from routers.project_insights import router as project_insights_router
from routers import (
    health, projects, items, test_db, clients, scrape,
    analysis, dashboard, project_dashboard, media_sources,
    project_media, thematic_area
)

load_dotenv()

app = FastAPI(
    title="Media Monitoring Backend",
    version="1.0.0",
    description="AI-powered media monitoring system"
)


@app.on_event("startup")
def startup_test():
    
    try:
        conn = get_db()
        conn.close()
        print("[STARTUP] Database connection OK")
        

    except Exception as e:
        print("[STARTUP ERROR] Database not available:", e)
        
@app.get("/")
async def root():
    return {"message": "Media Monitoring Backend is running.,"
    "see /docs for API documentation."}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTES
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

# REMOVE uvicorn.run — Ren  der must run uvicorn itself
