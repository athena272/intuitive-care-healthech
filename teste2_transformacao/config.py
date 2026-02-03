"""Configuracoes do Teste 2 - Transformacao e Validacao."""

import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CONSOLIDATED_CSV = os.path.join(DATA_DIR, "consolidado_despesas.csv")
CADOP_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/Relatorio_cadop.csv"
CADOP_LOCAL = os.path.join(DATA_DIR, "Relatorio_cadop.csv")
OUTPUT_CSV = "despesas_agregadas.csv"
OUTPUT_DIR = DATA_DIR
