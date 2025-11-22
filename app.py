from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers.project_insights import router as project_insights_router


from routers import (
    health, projects, items, test_db, clients, scrape, 
    analysis, dashboard,project_dashboard,media_sources,project_media,thematic_area
)

app = FastAPI(
    title="Media Monitoring Backend",
    version="1.0.0",
    description="AI-powered media monitoring system"
)

load_dotenv()

# ---------------------------
# FIXED: CORS MUST BE BEFORE ROUTERS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=False,   # IMPORTANT FIX
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# ROUTERS (after CORS)
# ---------------------------
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



