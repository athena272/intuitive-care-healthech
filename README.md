# Desafio Tecnico Intuitive Care - Healthtech

Implementacao do teste de entrada para estagiarios (v2.0): integracao com API ANS, transformacao e validacao de dados, banco de dados e API com interface web.

**Linguagem:** Python (backend e scripts). Vue.js no frontend. PostgreSQL no banco.

---

## Pre-requisitos

- Python 3.10+
- Docker e Docker Compose (para Teste 3 e 4)
- Node.js 18+ (para frontend Vue.js no Teste 4)

---

## Ambiente virtual (recomendado)

Use um ambiente virtual para instalar as dependencias do projeto e evitar conflitos com outros pacotes Python (por exemplo Streamlit, Jupyter) instalados no sistema.

**Criar e ativar o venv na raiz do projeto:**

```bash
# Windows (PowerShell ou CMD)
python -m venv .venv
.venv\Scripts\activate

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```
Com o ambiente ativado, o prompt mostrara algo como `(.venv)`. Instale as dependencias uma unica vez:

<img width="539" height="165" alt="image" src="https://github.com/user-attachments/assets/eddebd96-6b46-4417-a258-ee624e319d31" />

```bash
pip install -r requirements.txt
```

A partir daqui, execute os testes (Teste 1 à 4) **com o venv ativado**. Para desativar: `deactivate`.

---

## Como subir o banco (Docker)

Usado no **Teste 3** e **Teste 4**.

1. Instale [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/).
2. Copie o arquivo de exemplo de ambiente:
   ```bash
   copy .env.example .env
   ```
   (No Linux/macOS: `cp .env.example .env`)
3. Edite `.env` e defina `POSTGRES_PASSWORD` (e opcionalmente usuario/banco/porta).
4. Suba o container:
   ```bash
   docker-compose up -d
   ```
   Ou com Docker Compose v2: `docker compose up -d`
5. Verifique se o banco esta acessivel:
   - Com `psql`: `psql -h localhost -p 5432 -U ans_user -d ans_db` (use a senha do `.env`).
   - Ou use um cliente GUI (DBeaver, pgAdmin) com host=localhost, porta=5432, usuario e senha do `.env`.
6. Para parar: `docker-compose down` (ou `docker compose down`).

Usuario, senha e nome do banco sao definidos em `.env` (veja `.env.example`). Nunca commite o arquivo `.env`.

---

## Execução por teste

### Teste 1 - Integracao com API ANS

**Objetivo:** Baixar dados de Demonstracoes Contabeis (Despesas com Eventos/Sinistros) dos ultimos 3 trimestres da API ANS, consolidar em CSV e gerar `consolidado_despesas.zip`.

**Pre-requisitos:** Python 3.10+, dependencias em `requirements.txt` (recomendado: ambiente virtual ativado).

**Como rodar:**

```bash
# Se ainda nao instalou as dependencias (com venv ativado)
pip install -r requirements.txt

cd teste1_api_ans
python main.py
```

**Saida:** `data/consolidado_despesas.csv` e `data/consolidado_despesas.zip`.

<img width="1247" height="225" alt="image" src="https://github.com/user-attachments/assets/b902f56a-b24f-4c1b-8554-49148b822c67" />

<img width="284" height="278" alt="image" src="https://github.com/user-attachments/assets/bf98acc9-c501-4b96-825d-b6b7580d1d9f" />

---

### Teste 2 - Transformacao e Validacao

**Objetivo:** Validar e enriquecer o consolidado, agregar por operadora/UF e gerar `despesas_agregadas.csv`.

**Pre-requisitos:** Ter executado o Teste 1 (arquivo `data/consolidado_despesas.csv`).

**Como rodar:**

```bash
cd teste2_transformacao
python main.py
```

**Saida:** `data/despesas_agregadas.csv`.

<img width="842" height="168" alt="image" src="https://github.com/user-attachments/assets/ed178fe3-ef52-4fa0-8436-b1a2d1a1a022" />

<img width="224" height="276" alt="image" src="https://github.com/user-attachments/assets/64957c31-f926-433a-bc47-05ab72bd808b" />

---

### Teste 3 - Banco de Dados e Analise

**Pre-requisitos:** Docker com PostgreSQL rodando; CSVs em `data/` (Teste 1 e 2) e opcionalmente `data/Relatorio_cadop.csv` (baixado pelo Teste 1 ou 2).

**Como rodar:**

1. Subir o banco: `docker-compose up -d`
2. Aplicar DDL: `cd teste3_banco && python run_ddl.py`
3. Importar dados: `python import_csv.py`
4. (Opcional) Executar queries analiticas: `python run_queries.py`

Os arquivos gerados ficam em `data/`. As queries analiticas estao em `teste3_banco/queries/analiticas.sql`.

<img width="846" height="547" alt="image" src="https://github.com/user-attachments/assets/2c4f0a6d-1ba2-449f-b317-f44c68ad9620" />

---

### Teste 4 - API e Interface Web

**Pre-requisitos:** Banco populado (Teste 3). Python e Node.js.

**Backend (porta 8000):**

```bash
cd teste4_api_web/backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

<img width="1454" height="739" alt="image" src="https://github.com/user-attachments/assets/7d5a9eee-d0d5-42c8-a5ac-c51da28b3d6c" />

<img width="1031" height="172" alt="image" src="https://github.com/user-attachments/assets/1cc20f1a-f4af-426b-bc19-db9236d7afff" />

<img width="1033" height="434" alt="image" src="https://github.com/user-attachments/assets/8853d648-5bfc-45cb-9410-98bb5fb3f41b" />

**Frontend (porta 5173; proxy para /api no backend):**

```bash
cd teste4_api_web/frontend
npm install
npm run dev
```

<img width="627" height="556" alt="image" src="https://github.com/user-attachments/assets/d355c57c-dcb8-4c7f-b1ad-84575f76f5fd" />

Acesse http://localhost:5173. A colecao Postman esta em `teste4_api_web/postman/API_Operadoras_ANS.postman_collection.json` (variavel `base_url`: http://localhost:8000).

---

## Trade-offs tecnicos

### Teste 1

- **Processamento em memoria vs. incremental:** Optou-se por processar em memoria (pandas). Justificativa: volume dos ultimos 3 trimestres e tamanho dos ZIPs da ANS e compativel com memoria em maquinas tipicas; implementacao mais simples e suficiente para o escopo. Para volumes muito maiores, processamento por chunks ou streaming seria justificado.
- **CNPJs duplicados com razoes sociais diferentes:** Na consolidação, mantida a primeira ocorrencia por (CNPJ, Ano, Trimestre). Evita duplicidade de valor e mantém rastreabilidade por cadastro (Registro ANS -> CNPJ/Razao).
- **Valores zerados ou negativos:** Linhas com ValorDespesas <= 0 sao excluidas da consolidação (conta contabil 41 reflete despesa; zero/negativo nao faz sentido para o indicador).
- **Formato da fonte:** Os arquivos da ANS sao unico CSV por trimestre (ex.: 3T2025.csv) com colunas DATA, REG_ANS, CD_CONTA_CONTABIL, DESCRICAO, VL_SALDO_*. Filtro pela conta 41 (Despesas com Eventos/Sinistros). CNPJ e Razao Social obtidos via join com Relatorio_cadop (cadastro de operadoras).

### Teste 2

- **CNPJs invalidos:** Linhas com CNPJ invalido (formato ou digitos verificadores) sao rejeitadas. Pro: base limpa para analise. Contra: perda de registros; alternativa seria marcar como invalido e manter em tabela de rejeitados para auditoria.
- **Join com cadastro:** Feito em memoria (pandas). Registros sem match mantidos com RegistroANS/Modalidade/UF vazios. CNPJ com multiplas linhas no cadastro: primeira ocorrencia (keep='first').
- **Ordenacao:** Em memoria (sort_values), adequado ao volume apos agregacao.

### Teste 3

- **Normalizacao:** Tabelas normalizadas (operadoras, despesas_consolidado, despesas_agregadas). Justificativa: volume moderado, consultas por operadora/UF/trimestre; evita redundancia e facilita atualizacoes.
- **Tipos:** Valores monetarios em NUMERIC(18,2) (precisao; evita FLOAT). Ano/trimestre em SMALLINT. Chaves e identificadores em VARCHAR.
- **Query 1 (crescimento percentual):** Consideradas apenas operadoras com dado no primeiro e no ultimo trimestre do periodo; demais excluidas do ranking (evita divisao por zero e distorcao).
- **Query 3 (acima da media):** Abordagem com CTEs (media por trimestre, flag acima da media, contagem). Legibilidade e manutencao; performance adequada ao volume.

### Teste 4

- **Framework:** FastAPI. Justificativa: tipagem, documentacao automatica (/docs), desempenho e simplicidade para o tamanho do projeto.
- **Paginação:** Offset-based (page, limit). Simples de implementar e suficiente para o volume; cursor-based seria preferivel para listas muito grandes e atualizacoes frequentes.
- **Estatisticas:** Calculadas na hora (sem cache). Dados atualizados com pouca frequencia; consistencia imediata.
- **Formato de resposta:** Objeto com `data`, `total`, `page`, `limit` nas listas para permitir paginacao no frontend.
- **Frontend:** Busca/filtro no cliente (na pagina atual). Estado via composables/refs; tabela paginada via API. Grafico de despesas por UF com Chart.js. Tratamento de erros e loading com mensagens genericas (evita expor detalhes internos).

---

## Entrega

Compacte todo o projeto em um arquivo ZIP nomeado `Teste_{seu_nome}.zip`, incluindo codigo-fonte, README, requirements.txt, docker-compose.yml, .env.example, pastas teste1_api_ans a teste4_api_web (incluindo frontend e postman), e opcionalmente a pasta `data/` com os CSVs gerados (ou gere-os conforme as instrucoes acima).

---

## Licenca

Ver arquivo LICENSE.
