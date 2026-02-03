import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB


def get_conn():
    return psycopg2.connect(**DB, cursor_factory=RealDictCursor)
