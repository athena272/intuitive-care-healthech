"""
Pipeline Teste 1: Integracao com API ANS.
Baixa demonstracoes contabeis (ultimos 3 trimestres), processa Despesas com Eventos/Sinistros,
enriquece com cadastro de operadoras, consolida em CSV e gera consolidado_despesas.zip.
"""

import logging
import zipfile
from pathlib import Path

import requests

from config import OUTPUT_DIR, CONSOLIDATED_CSV, CONSOLIDATED_ZIP
from download import discover_quarter_zips, download_zips
from extract import extract_zip, find_despesas_files
from normalize import load_file, consolidate_with_rules, load_cadastral

CADOP_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def download_cadastral(dest_dir: Path) -> Path | None:
    """Baixa Relatorio_cadop.csv para dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / "Relatorio_cadop.csv"
    try:
        r = requests.get(CADOP_URL, timeout=60)
        r.raise_for_status()
        path.write_bytes(r.content)
        logger.info("Cadastro de operadoras baixado: %s", path)
        return path
    except Exception as e:
        logger.warning("Falha ao baixar cadastro: %s", e)
        return None


def run():
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Descobrindo ultimos trimestres...")
    quarter_list = discover_quarter_zips()
    if not quarter_list:
        raise RuntimeError("Nenhum trimestre encontrado na API ANS.")

    logger.info("Baixando ZIPs...")
    zip_paths = download_zips(quarter_list, dest_dir=output_dir)
    if not zip_paths:
        raise RuntimeError("Nenhum ZIP foi baixado.")

    cadastral_df = None
    cad_path = download_cadastral(output_dir)
    if cad_path and cad_path.exists():
        cadastral_df = load_cadastral(cad_path)
        if cadastral_df.empty:
            cadastral_df = None

    all_frames = []
    for zip_path in zip_paths:
        name = zip_path.stem
        if len(name) >= 5 and name[0].isdigit() and name[-4:].isdigit():
            trim = int(name[0])
            ano = int(name[-4:])
        else:
            trim, ano = 0, 0
        extract_dir = output_dir / f"extract_{name}"
        try:
            extract_zip(zip_path, extract_dir)
        except Exception as e:
            logger.warning("Falha ao extrair %s: %s", zip_path, e)
            continue
        files = list(extract_dir.rglob("*.csv")) + list(extract_dir.rglob("*.txt"))
        for f in files:
            if not f.is_file():
                continue
            df = load_file(f, ano, trim)
            if df is not None and not df.empty:
                all_frames.append(df)
                logger.info("Processado %s (%d linhas)", f.name, len(df))

    if not all_frames:
        raise RuntimeError("Nenhum dado de despesas processado. Verifique estrutura dos ZIPs.")

    consolidated = consolidate_with_rules(all_frames, cadastral_df)
    csv_path = output_dir / CONSOLIDATED_CSV
    consolidated.to_csv(csv_path, index=False, sep=";", encoding="utf-8")
    logger.info("CSV consolidado salvo: %s (%d linhas)", csv_path, len(consolidated))

    zip_out = output_dir / CONSOLIDATED_ZIP
    with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, CONSOLIDATED_CSV)
    logger.info("ZIP gerado: %s", zip_out)
    return csv_path, zip_out


if __name__ == "__main__":
    run()
