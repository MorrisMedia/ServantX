#!/usr/bin/env python3
"""Create the target Postgres database if it does not already exist."""

import os
from urllib.parse import urlparse

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

load_dotenv()


def create_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ℹ️ DATABASE_URL not set; skipping database creation")
        return

    normalized = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if not normalized.startswith("postgresql://"):
        print("ℹ️ Non-Postgres DATABASE_URL detected; skipping database creation")
        return

    parsed = urlparse(normalized)
    db_name = (parsed.path or "/postgres").lstrip("/") or "postgres"
    admin_db = os.getenv("POSTGRES_ADMIN_DB", "postgres")

    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            dbname=admin_db,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        if cursor.fetchone() is None:
            print(f"📦 Creating database {db_name}...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Database {db_name} created successfully")
        else:
            print(f"✅ Database {db_name} already exists")
    except Exception as exc:
        print(f"❌ Error creating database: {exc}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    create_db()
