import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass

DB = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
    "user": os.environ.get("POSTGRES_USER", "ans_user"),
    "password": os.environ.get("POSTGRES_PASSWORD", "ans_pass"),
    "dbname": os.environ.get("POSTGRES_DB", "ans_db"),
}
