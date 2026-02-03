"""Executa as queries analiticas e imprime os resultados (Teste 3.4)."""

import os
import re
from pathlib import Path

import psycopg2

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

QUERIES_DIR = Path(__file__).resolve().parent / "queries"


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ.get("POSTGRES_USER", "ans_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "ans_pass"),
        dbname=os.environ.get("POSTGRES_DB", "ans_db"),
    )


def main():
    conn = get_conn()
    path = QUERIES_DIR / "analiticas.sql"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Separa por ";" seguido de newline e comentario "Query" (cada bloco e uma query completa)
    blocks = re.split(r';\s*\n(?=\s*--\s*Query)', content)
    cur = conn.cursor()
    for i, block in enumerate(blocks):
        block = block.strip()
        if not block:
            continue
        # Nao pular blocos que sao queries (WITH ou SELECT), mesmo que comecem com comentario
        if block.startswith("--") and "WITH" not in block and "SELECT" not in block:
            continue
        stmt = block if block.rstrip().endswith(";") else block + ";"
        try:
            cur.execute(stmt)
            rows = cur.fetchall()
            if rows:
                colnames = [d[0] for d in cur.description]
                print("--- Query %d ---" % (i + 1))
                print(" | ".join(colnames))
                for row in rows:
                    print(" | ".join(str(x) for x in row))
                print()
        except Exception as e:
            print("Erro na query %d: %s" % (i + 1, e))
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
