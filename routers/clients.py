# backend/routers/clients.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database.connection import get_db
import uuid

router = APIRouter(prefix="/clients", tags=["Clients"])

# ------------------------------
# Pydantic model for validation
# ------------------------------
class ClientCreate(BaseModel):
    name: str
    contact_email: EmailStr | None = None


# ------------------------------
# POST: Create a new client
# ------------------------------
@router.post("/")
def create_client(client: ClientCreate):
    # Generate UUID for the client
    client_id = str(uuid.uuid4())

    try:
        conn = get_db()
        cursor = conn.cursor()

        sql = """
            INSERT INTO clients (id, name, contact_email)
            VALUES (%s, %s, %s)
        """

        values = (client_id, client.name, client.contact_email)

        cursor.execute(sql, values)
        conn.commit()

        return {
            "status": "success",
            "message": "Client created successfully",
            "data": {
                "id": client_id,
                "name": client.name,
                "contact_email": client.contact_email
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database insertion failed: {str(e)}"
        )

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


@router.get("/")
def list_clients():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, name FROM clients")
    clients = cursor.fetchall()

    cursor.close()
    conn.close()
    return clients
