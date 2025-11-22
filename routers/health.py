# backend/routers/health.py

from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/")
def check_health():
    return {"status": "ok", "message": "Backend running successfully"}
