"""Aplica o DDL (schema.sql) no banco. Execute apos subir o Docker e antes de import_csv.py."""

import os
from pathlib import Path

import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

DDL_PATH = Path(__file__).resolve().parent / "ddl" / "schema.sql"


def main():
    with open(DDL_PATH, "r", encoding="utf-8") as f:
        ddl = f.read()
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ.get("POSTGRES_USER", "ans_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "ans_pass"),
        dbname=os.environ.get("POSTGRES_DB", "ans_db"),
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(ddl)
    cur.close()
    conn.close()
    print("DDL aplicado com sucesso.")


if __name__ == "__main__":
    main()
