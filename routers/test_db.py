from fastapi import APIRouter
from database.connection import get_db

router = APIRouter(prefix="/test-db", tags=["Test Database"])

@router.get("/")
def test_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM projects")
    result = cursor.fetchone()
    conn.close()
    return {"projects_count": result[0]}
