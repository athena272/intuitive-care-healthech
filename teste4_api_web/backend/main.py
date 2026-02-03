"""
API Teste 4 - Operadoras e despesas.
FastAPI com paginacao offset-based; formato de resposta com metadados (data, total, page, limit).
Estatisticas calculadas na hora (dados atualizados com pouca frequencia).
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import get_conn

app = FastAPI(title="API Operadoras ANS", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/operadoras")
def listar_operadoras(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Lista operadoras com paginacao offset-based (por CNPJ para link de detalhe)."""
    offset = (page - 1) * limit
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(DISTINCT cnpj) AS total FROM despesas_consolidado"
        )
        total = cur.fetchone()["total"]
        cur.execute(
            """
            SELECT cnpj, MAX(razao_social) AS razao_social,
                   SUM(valor_despesas) AS valor_total
            FROM despesas_consolidado
            GROUP BY cnpj
            ORDER BY valor_total DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
        )
        rows = cur.fetchall()
        cur.close()
        return {
            "data": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "limit": limit,
        }
    finally:
        conn.close()


@app.get("/api/operadoras/{cnpj}")
def detalhe_operadora(cnpj: str):
    """Detalhes de uma operadora por CNPJ (apenas digitos)."""
    cnpj = "".join(c for c in cnpj if c.isdigit()).zfill(14)
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT registro_ans, cnpj, razao_social, modalidade, uf FROM operadoras WHERE cnpj = %s",
            (cnpj,),
        )
        row = cur.fetchone()
        if row:
            cur.close()
            return dict(row)
        cur.execute(
            """
            SELECT cnpj, MAX(razao_social) AS razao_social
            FROM despesas_consolidado WHERE cnpj = %s GROUP BY cnpj
            """,
            (cnpj,),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            raise HTTPException(status_code=404, detail="Operadora nao encontrada")
        return {"cnpj": row["cnpj"], "razao_social": row["razao_social"], "registro_ans": None, "modalidade": None, "uf": None}
    finally:
        conn.close()


@app.get("/api/operadoras/{cnpj}/despesas")
def despesas_operadora(cnpj: str):
    """Historico de despesas por trimestre da operadora (por CNPJ)."""
    cnpj = "".join(c for c in cnpj if c.isdigit()).zfill(14)
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT trimestre, ano, valor_despesas
            FROM despesas_consolidado
            WHERE cnpj = %s
            ORDER BY ano, trimestre
            """,
            (cnpj,),
        )
        rows = cur.fetchall()
        cur.close()
        return {"data": [dict(r) for r in rows]}
    finally:
        conn.close()


@app.get("/api/estatisticas")
def estatisticas():
    """Totais, media, top 5 operadoras e distribuicao por UF."""
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                COALESCE(SUM(valor_total), 0) AS total_despesas,
                COALESCE(AVG(valor_total), 0) AS media_despesas
            FROM despesas_agregadas
            """
        )
        agg = cur.fetchone()
        cur.execute(
            """
            SELECT razao_social, uf, valor_total
            FROM despesas_agregadas
            ORDER BY valor_total DESC
            LIMIT 5
            """
        )
        top5 = cur.fetchall()
        cur.execute(
            """
            SELECT uf, SUM(valor_total) AS total
            FROM despesas_agregadas
            WHERE uf IS NOT NULL AND uf <> ''
            GROUP BY uf
            ORDER BY total DESC
            """
        )
        por_uf = cur.fetchall()
        cur.close()
        return {
            "total_despesas": float(agg["total_despesas"] or 0),
            "media_despesas": float(agg["media_despesas"] or 0),
            "top_5_operadoras": [dict(r) for r in top5],
            "despesas_por_uf": [{"uf": r["uf"], "total": float(r["total"])} for r in por_uf],
        }
    finally:
        conn.close()


@app.get("/health")
def health():
    return {"status": "ok"}
