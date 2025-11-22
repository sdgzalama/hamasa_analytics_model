# routes/media_sources.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.connection import get_db
import uuid

router = APIRouter(prefix="/media-sources", tags=["Media Sources"])


# ----------------------------------
# DATA MODEL FOR INPUT
# ----------------------------------
class MediaSourceCreate(BaseModel):
    name: str
    base_url: str


# ----------------------------------
# GET: List Media Sources
# ----------------------------------
@router.get("/")
def list_sources():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name, base_url FROM media_sources")
    sources = cursor.fetchall()

    cursor.close()
    conn.close()
    return sources


# ----------------------------------
# POST: Create New Media Source
# ----------------------------------
@router.post("/")
def create_source(data: MediaSourceCreate):

    source_id = str(uuid.uuid4())
    conn = get_db()
    cursor = conn.cursor()

    sql = """
        INSERT INTO media_sources (id, name, base_url)
        VALUES (%s, %s, %s)
    """

    cursor.execute(sql, (source_id, data.name, data.base_url))
    conn.commit()

    cursor.close()
    conn.close()

    return {
        "status": "success",
        "message": "Media source added",
        "id": source_id,
        "name": data.name,
        "base_url": data.base_url
    }
