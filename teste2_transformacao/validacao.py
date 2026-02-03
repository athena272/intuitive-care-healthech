"""
Validacao de dados do consolidado (Teste 2.1).
- CNPJ: formato 14 digitos e digitos verificadores.
- Valores numericos positivos.
- Razao Social nao vazia.
Estrategia para CNPJs invalidos: rejeitar a linha (nao incluir no resultado).
Documentado no README: pros (dados consistentes) e contras (perda de registros).
"""

import re
import logging
from typing import Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def _digitos_verificadores_cnpj(cnpj_12: str) -> Tuple[str, str]:
    """Calcula os dois digitos verificadores do CNPJ (primeiros 12 digitos)."""
    if len(cnpj_12) != 12 or not cnpj_12.isdigit():
        return "", ""
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(c) * p for c, p in zip(cnpj_12, pesos1))
    d1 = 11 - (soma % 11)
    if d1 >= 10:
        d1 = 0
    cnpj_13 = cnpj_12 + str(d1)
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma2 = sum(int(c) * p for c, p in zip(cnpj_13, pesos2))
    d2 = 11 - (soma2 % 11)
    if d2 >= 10:
        d2 = 0
    return str(d1), str(d2)


def validar_cnpj(cnpj: str) -> bool:
    """Retorna True se CNPJ tem 14 digitos e digitos verificadores corretos."""
    digits = re.sub(r"\D", "", str(cnpj))
    if len(digits) != 14:
        return False
    d1_esp, d2_esp = _digitos_verificadores_cnpj(digits[:12])
    return digits[12] == d1_esp and digits[13] == d2_esp


def validar_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica validacoes e retorna apenas linhas validas.
    - CNPJ valido (formato + dv).
    - ValorDespesas > 0.
    - RazaoSocial nao vazia (apos strip).
    """
    if df.empty:
        return df
    col_cnpj = "CNPJ"
    col_razao = "RazaoSocial"
    col_valor = "ValorDespesas"
    for c in (col_cnpj, col_razao, col_valor):
        if c not in df.columns:
            logger.warning("Coluna %s ausente", c)
            return pd.DataFrame()
    df = df.copy()
    df[col_cnpj] = df[col_cnpj].astype(str).str.replace(r"\D", "", regex=True).str.zfill(14)
    mask_cnpj = df[col_cnpj].apply(validar_cnpj)
    mask_valor = pd.to_numeric(df[col_valor], errors="coerce") > 0
    mask_razao = df[col_razao].fillna("").astype(str).str.strip() != ""
    rejeitados = (~mask_cnpj).sum()
    if rejeitados > 0:
        logger.info("Linhas rejeitadas por CNPJ invalido: %d", rejeitados)
    return df.loc[mask_cnpj & mask_valor & mask_razao].reset_index(drop=True)
