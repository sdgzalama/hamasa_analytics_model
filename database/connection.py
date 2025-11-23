import mysql.connector
from mysql.connector import pooling
import os

connection_pool = None

def init_pool():
    global connection_pool

    if connection_pool is None:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="mypool",
            pool_size=3,
            pool_reset_session=True,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306)),
            connection_timeout=30
        )

def get_db():
    if connection_pool is None:
        init_pool()
    return connection_pool.get_connection()
