-- Teste 3 - DDL PostgreSQL
-- Abordagem: tabelas normalizadas (operadoras, despesas_consolidado, despesas_agregadas).
-- Justificativa: volume moderado, consultas analiticas por operadora/UF/trimestre; normalizacao evita redundancia e atualizacoes inconsistentes.
-- Tipos: valores monetarios em NUMERIC(18,2) (precisao; FLOAT evita-se por arredondamento); ano/trimestre em SMALLINT; datas nao usadas como filtro mantidas como VARCHAR para flexibilidade de importacao.

DROP TABLE IF EXISTS despesas_agregadas;
DROP TABLE IF EXISTS despesas_consolidado;
DROP TABLE IF EXISTS operadoras;

-- Cadastro de operadoras (fonte: Relatorio_cadop)
CREATE TABLE operadoras (
    registro_ans VARCHAR(20) NOT NULL,
    cnpj VARCHAR(14) NOT NULL,
    razao_social VARCHAR(500),
    modalidade VARCHAR(200),
    uf CHAR(2),
    PRIMARY KEY (cnpj),
    UNIQUE (registro_ans)
);
CREATE INDEX idx_operadoras_uf ON operadoras(uf);
CREATE INDEX idx_operadoras_razao ON operadoras(razao_social);

-- Despesas consolidadas por trimestre (fonte: consolidado_despesas.csv)
CREATE TABLE despesas_consolidado (
    id SERIAL PRIMARY KEY,
    cnpj VARCHAR(14) NOT NULL,
    razao_social VARCHAR(500),
    trimestre SMALLINT NOT NULL,
    ano SMALLINT NOT NULL,
    valor_despesas NUMERIC(18, 2) NOT NULL,
    CONSTRAINT chk_valor_positivo CHECK (valor_despesas >= 0),
    CONSTRAINT chk_trimestre CHECK (trimestre BETWEEN 1 AND 4),
    CONSTRAINT chk_ano CHECK (ano >= 2000 AND ano <= 2100)
);
CREATE INDEX idx_despesas_cons_cnpj ON despesas_consolidado(cnpj);
CREATE INDEX idx_despesas_cons_ano_trim ON despesas_consolidado(ano, trimestre);
CREATE INDEX idx_despesas_cons_razao ON despesas_consolidado(razao_social);

-- Despesas agregadas por RazaoSocial e UF (fonte: despesas_agregadas.csv)
CREATE TABLE despesas_agregadas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(500) NOT NULL,
    uf CHAR(2),
    valor_total NUMERIC(18, 2) NOT NULL,
    media_por_trimestre NUMERIC(18, 2),
    desvio_padrao_despesas NUMERIC(18, 2),
    CONSTRAINT chk_valor_total_positivo CHECK (valor_total >= 0)
);
CREATE INDEX idx_despesas_agr_uf ON despesas_agregadas(uf);
CREATE INDEX idx_despesas_agr_razao ON despesas_agregadas(razao_social);
CREATE INDEX idx_despesas_agr_valor ON despesas_agregadas(valor_total DESC);
