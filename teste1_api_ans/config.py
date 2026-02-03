"""Configuracoes do pipeline Teste 1 - API ANS."""

import os

BASE_URL = "https://dadosabertos.ans.gov.br/FTP/PDA/demonstracoes_contabeis"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CONSOLIDATED_CSV = "consolidado_despesas.csv"
CONSOLIDATED_ZIP = "consolidado_despesas.zip"
NUM_QUARTERS = 3

# Palavras-chave para identificar arquivos de Despesas com Eventos/Sinistros
DESPESAS_SINISTROS_KEYWORDS = ("despesas", "eventos", "sinistros", "despesa", "sinistro", "evento")
