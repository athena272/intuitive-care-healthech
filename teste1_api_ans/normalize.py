"""Normalizacao de arquivos para schema: CNPJ, RazaoSocial, Trimestre, Ano, ValorDespesas."""

import re
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

TARGET_COLUMNS = ["CNPJ", "RazaoSocial", "Trimestre", "Ano", "ValorDespesas"]

# Conta contabil ANS para "Despesas com Eventos/Sinistros" (EVENTOS INDENIZAVEIS LIQUIDOS / SINISTROS RETIDOS)
CONTA_DESPESAS_EVENTOS_SINISTROS = "41"


def _normalize_cnpj(val) -> str:
    """Extrai apenas digitos do CNPJ."""
    if pd.isna(val):
        return ""
    s = re.sub(r"\D", "", str(val).strip())
    return s[:14].zfill(14) if len(s) >= 14 else s.zfill(14)


def _parse_trimestre_from_data(data_str: str) -> tuple[int, int]:
    """De DATA no formato YYYY-MM-DD retorna (ano, trimestre)."""
    try:
        parts = str(data_str).strip()[:10].split("-")
        if len(parts) == 3:
            ano = int(parts[0])
            mes = int(parts[1])
            if 1 <= mes <= 3:
                trim = 1
            elif 4 <= mes <= 6:
                trim = 2
            elif 7 <= mes <= 9:
                trim = 3
            else:
                trim = 4
            if 2000 <= ano <= 2100:
                return ano, trim
    except (ValueError, TypeError):
        pass
    return 0, 0


def load_demonstracoes_ans(path: Path, ano: int, trimestre: int) -> pd.DataFrame | None:
    """
    Carrega CSV no formato ANS (DATA, REG_ANS, CD_CONTA_CONTABIL, DESCRICAO, VL_SALDO_INICIAL, VL_SALDO_FINAL).
    Filtra pela conta de Despesas com Eventos/Sinistros (conta 41) e retorna REG_ANS, Ano, Trimestre, ValorDespesas.
    """
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path, sep=";", encoding=enc, decimal=",", low_memory=False)
            break
        except Exception as e:
            logger.debug("Encoding %s em %s: %s", enc, path, e)
            continue
    else:
        return None
    if df.empty:
        return None
    df.columns = [str(c).strip().upper() for c in df.columns]
    required = {"REG_ANS", "CD_CONTA_CONTABIL", "VL_SALDO_FINAL"}
    if not required.issubset(set(df.columns)):
        return None
    mask = df["CD_CONTA_CONTABIL"].astype(str).str.strip() == CONTA_DESPESAS_EVENTOS_SINISTROS
    df = df.loc[mask, ["REG_ANS", "VL_SALDO_FINAL"]].copy()
    df = df.rename(columns={"VL_SALDO_FINAL": "ValorDespesas"})
    df["ValorDespesas"] = pd.to_numeric(df["ValorDespesas"], errors="coerce").fillna(0)
    df["Ano"] = ano
    df["Trimestre"] = trimestre
    df["REG_ANS"] = df["REG_ANS"].astype(str).str.strip().str.replace('"', "")
    return df[["REG_ANS", "Ano", "Trimestre", "ValorDespesas"]]


def load_file(path: Path, ano: int, trimestre: int) -> pd.DataFrame | None:
    """
    Carrega um arquivo (CSV no formato ANS ou generico) e normaliza para schema com REG_ANS, Ano, Trimestre, ValorDespesas.
    Para formato ANS (colunas DATA, REG_ANS, CD_CONTA_CONTABIL, DESCRICAO, VL_*), usa load_demonstracoes_ans.
    """
    suf = path.suffix.lower()
    if suf not in (".csv", ".txt"):
        return None
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            peek = path.read_text(encoding=enc).split("\n")[0][:500]
            break
        except Exception:
            continue
    else:
        return None
    cols_upper = peek.upper()
    if "REG_ANS" in cols_upper and "CD_CONTA_CONTABIL" in cols_upper and "VL_SALDO_FINAL" in cols_upper:
        return load_demonstracoes_ans(path, ano, trimestre)
    return _load_file_generic(path, ano, trimestre)


def _load_file_generic(path: Path, ano: int, trimestre: int) -> pd.DataFrame | None:
    """Fallback para CSVs com colunas CNPJ, Razao Social, valor."""
    import pandas as pd
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            sep = ";" if ";" in path.read_text(encoding=enc).split("\n")[0] else ","
            df = pd.read_csv(path, sep=sep, encoding=enc, decimal=",", low_memory=False)
            break
        except Exception:
            continue
    else:
        return None
    if df.empty:
        return None
    df = df.rename(columns=lambda x: str(x).strip() if isinstance(x, str) else x)
    cnpj_col = next((c for c in df.columns if "cnpj" in str(c).lower()), None)
    razao_col = next((c for c in df.columns if "razao" in str(c).lower() or "social" in str(c).lower() or "denominacao" in str(c).lower()), None)
    value_col = next((c for c in df.columns if "valor" in str(c).lower() or "despesa" in str(c).lower()), None)
    if not cnpj_col or not value_col:
        return None
    out = pd.DataFrame()
    out["CNPJ"] = df[cnpj_col].astype(str).map(lambda v: re.sub(r"\D", "", str(v))[:14].zfill(14) if pd.notna(v) else "")
    out["RazaoSocial"] = df[razao_col].fillna("").astype(str).str.strip() if razao_col else ""
    out["Trimestre"] = trimestre
    out["Ano"] = ano
    out["ValorDespesas"] = pd.to_numeric(df[value_col].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    out = out[out["CNPJ"].str.len() >= 14]
    return out


def consolidate_with_rules(
    frames: list[pd.DataFrame], cadastral_df: pd.DataFrame | None = None
) -> pd.DataFrame:
    """
    Consolida listas de DataFrames. Se os frames tiverem REG_ANS, faz join com cadastral_df para obter CNPJ e RazaoSocial.
    Regras: valores <= 0 removidos; duplicatas (CNPJ, Ano, Trimestre) mantem primeira; ordenacao por Ano, Trimestre, CNPJ.
    """
    if not frames:
        return pd.DataFrame(columns=TARGET_COLUMNS)
    concat = pd.concat(frames, ignore_index=True)
    concat = concat[concat["ValorDespesas"] > 0].copy()
    if "REG_ANS" in concat.columns and cadastral_df is not None and not cadastral_df.empty:
        reg_col = next((c for c in cadastral_df.columns if "registro" in str(c).lower() or c == "Registro_ANS"), None)
        cnpj_col = next((c for c in cadastral_df.columns if "cnpj" in str(c).lower()), None)
        razao_col = next((c for c in cadastral_df.columns if "razao" in str(c).lower() or "razao_social" in str(c).lower() or "denominacao" in str(c).lower()), None)
        if reg_col and cnpj_col:
            cad = cadastral_df[[reg_col, cnpj_col]].copy()
            cad.columns = ["REG_ANS", "CNPJ"]
            cad["REG_ANS"] = cad["REG_ANS"].astype(str).str.strip().str.replace('"', "")
            cad["CNPJ"] = cad["CNPJ"].astype(str).map(lambda v: re.sub(r"\D", "", str(v))[:14].zfill(14))
            if razao_col:
                cad["RazaoSocial"] = cadastral_df[razao_col].fillna("").astype(str).str.strip()
            else:
                cad["RazaoSocial"] = ""
            cad = cad.drop_duplicates(subset=["REG_ANS"], keep="first")
            concat = concat.merge(cad, on="REG_ANS", how="left")
            concat = concat[concat["CNPJ"].notna() & (concat["CNPJ"].astype(str).str.len() >= 14)]
    if "CNPJ" not in concat.columns:
        concat["CNPJ"] = ""
        concat["RazaoSocial"] = ""
    concat = concat.drop_duplicates(subset=["CNPJ", "Ano", "Trimestre"], keep="first")
    concat = concat.sort_values(["Ano", "Trimestre", "CNPJ"]).reset_index(drop=True)
    for col in TARGET_COLUMNS:
        if col not in concat.columns:
            concat[col] = ""
    return concat[TARGET_COLUMNS]


def load_cadastral(csv_path: Path) -> pd.DataFrame:
    """Carrega CSV cadastral das operadoras (Relatorio_cadop ou similar)."""
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(csv_path, sep=";", encoding=enc, low_memory=False)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception:
            continue
    return pd.DataFrame()
