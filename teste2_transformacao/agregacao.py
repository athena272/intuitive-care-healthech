"""
Agregacao por RazaoSocial e UF (Teste 2.3).
Total de despesas, media por trimestre, desvio padrao; ordenacao por valor total (maior para menor).
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def agregar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa por RazaoSocial e UF; calcula total, media por trimestre e desvio padrao das despesas.
    Ordena por valor total decrescente.
    """
    if df.empty or "ValorDespesas" not in df.columns:
        return pd.DataFrame()
    group_cols = ["RazaoSocial", "UF"]
    for c in group_cols:
        if c not in df.columns:
            df[c] = ""
    df["ValorDespesas"] = pd.to_numeric(df["ValorDespesas"], errors="coerce").fillna(0)
    agg = df.groupby(group_cols, as_index=False).agg(
        total_despesas=("ValorDespesas", "sum"),
        media_por_trimestre=("ValorDespesas", "mean"),
        desvio_padrao_despesas=("ValorDespesas", "std"),
    )
    agg = agg.rename(columns={
        "total_despesas": "ValorTotal",
        "media_por_trimestre": "MediaPorTrimestre",
        "desvio_padrao_despesas": "DesvioPadraoDespesas",
    })
    agg["DesvioPadraoDespesas"] = agg["DesvioPadraoDespesas"].fillna(0)
    agg = agg.sort_values("ValorTotal", ascending=False).reset_index(drop=True)
    return agg
