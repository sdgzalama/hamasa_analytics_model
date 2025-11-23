import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

dbconfig = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "connection_timeout": 30
}

connection_pool = pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=3,      # InfinityFree cannot handle 10 connections
    pool_reset_session=True,
    **dbconfig
)

def get_db():
    try:
        conn = connection_pool.get_connection()
        return conn
    except Exception as e:
        print("DB ERROR:", e)
        raise
