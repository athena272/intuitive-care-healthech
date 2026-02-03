"""Extracao de arquivos ZIP e identificacao dos arquivos de Despesas com Eventos/Sinistros."""

import zipfile
import logging
from pathlib import Path

from config import DESPESAS_SINISTROS_KEYWORDS

logger = logging.getLogger(__name__)


def _matches_despesas_sinistros(name: str, first_line: str) -> bool:
    """Verifica se nome ou cabecalho sugerem dados de Despesas com Eventos/Sinistros."""
    name_lower = name.lower()
    line_lower = (first_line or "").lower()
    combined = name_lower + " " + line_lower
    return any(kw in combined for kw in DESPESAS_SINISTROS_KEYWORDS)


def extract_zip(zip_path: Path, out_dir: Path) -> Path:
    """Extrai zip_path em out_dir. Retorna o diretorio onde foi extraido."""
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out_dir)
    return out_dir


def find_despesas_files(extract_dir: Path) -> list[Path]:
    """
    Percorre extract_dir e retorna arquivos que parecem conter dados de
    Despesas com Eventos/Sinistros (por nome ou primeira linha).
    """
    found = []
    for path in extract_dir.rglob("*"):
        if not path.is_file():
            continue
        suf = path.suffix.lower()
        if suf not in (".csv", ".txt", ".xlsx", ".xls"):
            continue
        first_line = ""
        try:
            if suf == ".xlsx" or suf == ".xls":
                import pandas as pd
                df = pd.read_excel(path, nrows=1, header=0)
                first_line = " ".join(df.astype(str).values.flatten().tolist()) if not df.empty else ""
            else:
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        first_line = path.read_text(encoding=enc).split("\n")[0][:2000]
                        break
                    except Exception:
                        continue
        except Exception as e:
            logger.debug("Leitura de cabecalho %s: %s", path, e)
        if _matches_despesas_sinistros(path.name, first_line):
            found.append(path)
    if not found:
        # Fallback: qualquer CSV/TXT no diretorio que tenha coluna de valor e identificador
        for path in extract_dir.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in (".csv", ".txt"):
                continue
            try:
                for enc in ("utf-8", "latin-1", "cp1252"):
                    try:
                        line = path.read_text(encoding=enc).split("\n")[0][:1500]
                        if "cnpj" in line.lower() and ("valor" in line.lower() or "despesa" in line.lower()):
                            found.append(path)
                            break
                    except Exception:
                        continue
            except Exception:
                pass
    return list(dict.fromkeys(found))
