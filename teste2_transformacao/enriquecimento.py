"""
Enriquecimento com dados cadastrais (Teste 2.2).
Join por CNPJ com Relatorio_cadop; adiciona RegistroANS, Modalidade, UF.
Registros sem match: mantidos com NULL nessas colunas (nao excluimos para nao perder despesas).
CNPJ com multiplas linhas no cadastro: primeira ocorrencia por CNPJ (keep='first').
"""

import re
import logging
from pathlib import Path

import pandas as pd
import requests

from config import CADOP_URL, CADOP_LOCAL

logger = logging.getLogger(__name__)


def baixar_cadastral_se_necessario() -> Path | None:
    path = Path(CADOP_LOCAL)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = requests.get(CADOP_URL, timeout=60)
        r.raise_for_status()
        path.write_bytes(r.content)
        logger.info("Cadastro baixado: %s", path)
        return path
    except Exception as e:
        logger.warning("Falha ao baixar cadastro: %s", e)
        return None


def enriquecer(df: pd.DataFrame, cadastro_path: Path | None) -> pd.DataFrame:
    """
    Faz left join por CNPJ com o cadastro; adiciona RegistroANS, Modalidade, UF.
    """
    df = df.copy()
    df["CNPJ_norm"] = df["CNPJ"].astype(str).str.replace(r"\D", "", regex=True).str.zfill(14)
    if cadastro_path is None or not cadastro_path.exists():
        df["RegistroANS"] = ""
        df["Modalidade"] = ""
        df["UF"] = ""
        df = df.drop(columns=["CNPJ_norm"], errors="ignore")
        return df
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            cad = pd.read_csv(cadastro_path, sep=";", encoding=enc, low_memory=False)
            break
        except Exception:
            continue
    else:
        df = df.drop(columns=["CNPJ_norm"], errors="ignore")
        return df
    cols = {str(c).strip(): c for c in cad.columns}
    cnpj_cad = next((cols[k] for k in cols if "cnpj" in k.lower()), None)
    if cnpj_cad is None:
        df["RegistroANS"] = ""
        df["Modalidade"] = ""
        df["UF"] = ""
        df = df.drop(columns=["CNPJ_norm"], errors="ignore")
        return df
    reg_cad = next((cols[k] for k in cols if "registro" in k.lower() and "ans" in k.lower()), None) or next((cols[k] for k in cols if "registro" in k.lower() and "operadora" in k.lower()), None)
    mod_cad = next((cols[k] for k in cols if "modalidade" in k.lower()), None)
    uf_cad = next((cols[k] for k in cols if k.upper() == "UF"), None)
    cad["CNPJ_norm"] = cad[cnpj_cad].astype(str).str.replace(r"\D", "", regex=True).str.zfill(14)
    cad = cad.drop_duplicates(subset=["CNPJ_norm"], keep="first")
    sel = ["CNPJ_norm"]
    if reg_cad is not None:
        cad["RegistroANS"] = cad[reg_cad].astype(str)
        sel.append("RegistroANS")
    if mod_cad is not None:
        cad["Modalidade"] = cad[mod_cad].fillna("").astype(str)
        sel.append("Modalidade")
    if uf_cad is not None:
        cad["UF"] = cad[uf_cad].fillna("").astype(str)
        sel.append("UF")
    cad = cad[[c for c in sel if c in cad.columns]]
    out = df.merge(cad, on="CNPJ_norm", how="left")
    for c in ("RegistroANS", "Modalidade", "UF"):
        if c in out.columns:
            out[c] = out[c].fillna("").astype(str)
        else:
            out[c] = ""
    out = out.drop(columns=["CNPJ_norm"], errors="ignore")
    return out
