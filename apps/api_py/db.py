import os
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    """
    Creates a new DB connection using DATABASE_URL from .env.
    One connection per request (simple and clear).
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set. Did you create apps/api_py/.env ?")

    parsed = urlparse(db_url)
    if parsed.scheme not in ("postgresql", "postgres"):
        raise RuntimeError("DATABASE_URL must start with postgresql://")

    return psycopg2.connect(
        dbname=(parsed.path or "").lstrip("/"),
        user=parsed.username,
        password=parsed.password,
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        cursor_factory=RealDictCursor,
    )
