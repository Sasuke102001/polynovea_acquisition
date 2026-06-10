"""
apply_migrations.py — Apply all SQL migrations in Database/sql/ in filename order.

Migrations are written idempotently (CREATE TABLE IF NOT EXISTS / ADD COLUMN IF
NOT EXISTS), so this is safe to run on every pipeline pass. Files run in
lexical order: 001_init_schema.sql, 002_ml_upgrade.sql, ...
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")

for p in [Path(__file__).parent.parent.parent / ".env",
          Path(__file__).parent.parent.parent.parent / "App" / "backend" / ".env"]:
    if p.exists():
        load_dotenv(p)
        break

DB_CONFIG = {
    "host":     os.getenv("PG_HOST",     "polynovea-module2.cxeo8066g8t2.ap-south-1.rds.amazonaws.com"),
    "port":     int(os.getenv("PG_PORT", 5432)),
    "dbname":   os.getenv("PG_DB",       "polynovea_module2"),
    "user":     os.getenv("PG_USER",     "polynovea_admin"),
    "password": os.getenv("PG_PASSWORD", ""),
    "sslmode":  "require",
}

SQL_DIR = Path(__file__).resolve().parent.parent.parent / "sql"


def main():
    print("\napply_migrations.py — Applying SQL migrations\n")
    files = sorted(SQL_DIR.glob("*.sql"))
    if not files:
        print(f"  No .sql files found in {SQL_DIR}")
        return

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        for sql_file in files:
            sql = sql_file.read_text(encoding="utf-8")
            with conn.cursor() as cursor:
                cursor.execute(sql)
            conn.commit()
            print(f"  Applied {sql_file.name}")
    finally:
        conn.close()
    print(f"\n  {len(files)} migration file(s) applied.")


if __name__ == "__main__":
    main()
