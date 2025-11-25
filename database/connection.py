import mysql.connector
from mysql.connector import pooling, Error
import os
import time

connection_pool = None

def init_pool():
    """
    (Re)Initialize a new MySQL connection pool.
    """
    global connection_pool

    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=5,
            pool_reset_session=True,
            host="srv526.hstgr.io",
            user="u855436630_media_user",
            password="u1C^/o|A0p>Y",
            database="u855436630_media_m_db",
            port=int(os.getenv("DB_PORT", 3306)),
            connection_timeout=30
        )
        print("[DB] Connection pool initialized")

    except Error as e:
        print("[DB ERROR] Pool init failed:", e)
        raise


def get_db(retries=3, delay=2):
    """
    Safely get a DB connection with retries.
    Automatically resets pool if needed.
    """
    global connection_pool

    for attempt in range(1, retries + 1):
        try:
            # Initialize pool if missing
            if connection_pool is None:
                init_pool()

            # Try getting a connection
            conn = connection_pool.get_connection()

            # If connection is closed or broken, recreate pool
            if not conn.is_connected():
                print("[DB WARNING] Connection not active, recreating pool...")
                init_pool()
                continue

            return conn

        except Error as e:
            print("Real database error:", repr(e))

            # Reset pool on errors
            connection_pool = None

            if attempt < retries:
                time.sleep(delay)
            else:
                # Final failure -> re-raise so FastAPI shows clean error
                raise RuntimeError("Database is unavailable. Please try again shortly.")

    # Should never reach here
    raise RuntimeError("Database connection logic failed unexpectedly.")
