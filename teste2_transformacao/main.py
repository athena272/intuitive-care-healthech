"""
Pipeline Teste 2: Transformacao e Validacao.
Le o consolidado_despesas.csv (do Teste 1), valida, enriquece com cadastro,
agrega por RazaoSocial/UF e gera despesas_agregadas.csv.
"""

import logging
import os
import zipfile
from pathlib import Path

import pandas as pd

from config import CONSOLIDATED_CSV, OUTPUT_CSV, OUTPUT_DIR
from validacao import validar_df
from enriquecimento import baixar_cadastral_se_necessario, enriquecer
from agregacao import agregar

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def run():
    path_consolidado = Path(CONSOLIDATED_CSV)
    if not path_consolidado.exists():
        raise FileNotFoundError(
            "Arquivo consolidado nao encontrado: %s. Execute antes o Teste 1 (teste1_api_ans/main.py)." % CONSOLIDATED_CSV
        )
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(path_consolidado, sep=";", encoding=enc)
            break
        except Exception as e:
            logger.debug("Encoding %s: %s", enc, e)
            continue
    else:
        raise RuntimeError("Nao foi possivel ler o consolidado (encoding).")
    logger.info("Consolidado carregado: %d linhas", len(df))
    df = validar_df(df)
    logger.info("Apos validacao: %d linhas", len(df))
    cad_path = baixar_cadastral_se_necessario()
    df = enriquecer(df, cad_path)
    agg = agregar(df)
    out_dir = Path(OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_out = out_dir / OUTPUT_CSV
    agg.to_csv(csv_out, index=False, sep=";", encoding="utf-8")
    logger.info("Arquivo salvo: %s (%d linhas)", csv_out, len(agg))
    logger.info("Para a entrega, compacte o projeto (ou os artefatos indicados) em Teste_{seu_nome}.zip")
    return csv_out


if __name__ == "__main__":
    run()
