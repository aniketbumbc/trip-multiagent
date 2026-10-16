import os

import psycopg
from dotenv import load_dotenv

load_dotenv()


def check_db_connectivity() -> bool:
    """Return True when the database accepts a connection and a simple query."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    with psycopg.connect(database_url, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            row = cur.fetchone()

    return row is not None and row[0] == 1


if __name__ == "__main__":
    try:
        ok = check_db_connectivity()
    except Exception as exc:
        print(f"Database connection failed: {exc}")
        raise SystemExit(1) from exc

    print("Database connection ok" if ok else "Database connection failed")
