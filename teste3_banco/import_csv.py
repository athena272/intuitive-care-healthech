"""
Importacao dos CSVs para o banco PostgreSQL (Teste 3.3).
Encoding UTF-8; tratamento: NULL em obrigatorios -> rejeitar linha; string em numerico -> tentar conversao, senao rejeitar; datas inconsistentes -> normalizar ano/trimestre quando possivel.
"""

import os
import re
import logging
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Carrega .env da raiz do projeto
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONSOLIDATED = DATA_DIR / "consolidado_despesas.csv"
AGREGADAS = DATA_DIR / "despesas_agregadas.csv"
CADOP = DATA_DIR / "Relatorio_cadop.csv"


def get_conn():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        user=os.environ.get("POSTGRES_USER", "ans_user"),
        password=os.environ.get("POSTGRES_PASSWORD", "ans_pass"),
        dbname=os.environ.get("POSTGRES_DB", "ans_db"),
    )


def _normalize_cnpj(v):
    if pd.isna(v):
        return None
    s = re.sub(r"\D", "", str(v).strip())
    return s[:14].zfill(14) if len(s) >= 14 else None


def _to_num(v, default=None):
    if pd.isna(v) or v == "":
        return default
    try:
        if isinstance(v, str):
            v = v.replace(",", ".")
        return float(v)
    except (ValueError, TypeError):
        return default


def _to_int(v, default=None):
    n = _to_num(v, default)
    return int(n) if n is not None else default


def import_operadoras(conn):
    if not CADOP.exists():
        logger.warning("Cadastro nao encontrado: %s. Pulando tabela operadoras.", CADOP)
        return 0
    df = pd.read_csv(CADOP, sep=";", encoding="utf-8", low_memory=False)
    cols = {str(c).strip(): c for c in df.columns}
    reg = next((cols[k] for k in cols if "registro" in k.lower() and ("ans" in k.lower() or "operadora" in k.lower())), None)
    cnpj = next((cols[k] for k in cols if "cnpj" in k.lower()), None)
    razao = next((cols[k] for k in cols if "razao" in k.lower() and "social" in k.lower()), None)
    mod = next((cols[k] for k in cols if "modalidade" in k.lower()), None)
    uf = next((cols[k] for k in cols if k.upper() == "UF"), None)
    if not reg or not cnpj:
        logger.warning("Colunas registro/cnpj nao encontradas no cadastro.")
        return 0
    rows = []
    for _, r in df.iterrows():
        cnpj_val = _normalize_cnpj(r.get(cnpj))
        if not cnpj_val:
            continue
        reg_val = str(r.get(reg, "")).strip() or None
        if not reg_val:
            continue
        razao_val = str(r.get(razao, "")).strip()[:500] if razao else None
        mod_val = str(r.get(mod, "")).strip()[:200] if mod else None
        uf_val = str(r.get(uf, "")).strip()[:2] if uf else None
        rows.append((reg_val, cnpj_val, razao_val, mod_val, uf_val))
    if not rows:
        return 0
    cur = conn.cursor()
    try:
        execute_values(
            cur,
            """INSERT INTO operadoras (registro_ans, cnpj, razao_social, modalidade, uf)
               VALUES %s ON CONFLICT (cnpj) DO UPDATE SET
               registro_ans = EXCLUDED.registro_ans, razao_social = EXCLUDED.razao_social,
               modalidade = EXCLUDED.modalidade, uf = EXCLUDED.uf""",
            rows,
            page_size=1000,
        )
        conn.commit()
        return len(rows)
    finally:
        cur.close()


def import_consolidado(conn):
    if not CONSOLIDATED.exists():
        logger.warning("Consolidado nao encontrado: %s", CONSOLIDATED)
        return 0
    df = pd.read_csv(CONSOLIDATED, sep=";", encoding="utf-8")
    rows = []
    for _, r in df.iterrows():
        cnpj_val = _normalize_cnpj(r.get("CNPJ"))
        if not cnpj_val:
            continue
        razao_val = str(r.get("RazaoSocial", "")).strip()[:500] or None
        trim = _to_int(r.get("Trimestre"), 0)
        ano = _to_int(r.get("Ano"), 0)
        if trim not in (1, 2, 3, 4) or ano < 2000:
            continue
        val = _to_num(r.get("ValorDespesas"), -1)
        if val is None or val < 0:
            continue
        rows.append((cnpj_val, razao_val, trim, ano, round(val, 2)))
    if not rows:
        return 0
    cur = conn.cursor()
    try:
        execute_values(
            cur,
            """INSERT INTO despesas_consolidado (cnpj, razao_social, trimestre, ano, valor_despesas) VALUES %s""",
            rows,
            page_size=1000,
        )
        conn.commit()
        return len(rows)
    finally:
        cur.close()


def import_agregadas(conn):
    if not AGREGADAS.exists():
        logger.warning("Agregadas nao encontrado: %s", AGREGADAS)
        return 0
    df = pd.read_csv(AGREGADAS, sep=";", encoding="utf-8")
    rows = []
    for _, r in df.iterrows():
        razao_val = str(r.get("RazaoSocial", "")).strip()[:500]
        if not razao_val:
            continue
        uf_val = str(r.get("UF", "")).strip()[:2] or None
        vt = _to_num(r.get("ValorTotal"), -1)
        if vt is None or vt < 0:
            continue
        media = _to_num(r.get("MediaPorTrimestre"))
        desvio = _to_num(r.get("DesvioPadraoDespesas"))
        rows.append((razao_val, uf_val, round(vt, 2), round(media, 2) if media is not None else None, round(desvio, 2) if desvio is not None else None))
    if not rows:
        return 0
    cur = conn.cursor()
    try:
        execute_values(
            cur,
            """INSERT INTO despesas_agregadas (razao_social, uf, valor_total, media_por_trimestre, desvio_padrao_despesas) VALUES %s""",
            rows,
            page_size=1000,
        )
        conn.commit()
        return len(rows)
    finally:
        cur.close()


def run():
    logger.info("Conectando ao banco...")
    conn = get_conn()
    try:
        n_op = import_operadoras(conn)
        logger.info("Operadoras: %d linhas", n_op)
        n_cons = import_consolidado(conn)
        logger.info("Despesas consolidado: %d linhas", n_cons)
        n_agr = import_agregadas(conn)
        logger.info("Despesas agregadas: %d linhas", n_agr)
    finally:
        conn.close()


if __name__ == "__main__":
    run()
