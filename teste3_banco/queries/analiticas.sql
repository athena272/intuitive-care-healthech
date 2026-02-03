-- Teste 3.4 - Queries analiticas
-- Convencao: operadoras sem dados em algum trimestre sao excluidas do calculo de crescimento (Query 1);
-- assim so entram operadoras com valor no primeiro E no ultimo trimestre do periodo analisado.

-- Query 1: Top 5 operadoras com maior crescimento percentual de despesas entre o primeiro e o ultimo trimestre analisado.
-- Consideramos apenas operadoras que possuem dado no primeiro E no ultimo trimestre (evita divisao por zero e interpretacoes distorcidas).
WITH periodos AS (
    SELECT MIN(ano * 10 + trimestre) AS first_p, MAX(ano * 10 + trimestre) AS last_p
    FROM despesas_consolidado
),
primeiro_ultimo AS (
    SELECT
        cnpj,
        razao_social,
        SUM(CASE WHEN (ano * 10 + trimestre) = (SELECT first_p FROM periodos) THEN valor_despesas ELSE 0 END) AS valor_primeiro,
        SUM(CASE WHEN (ano * 10 + trimestre) = (SELECT last_p FROM periodos) THEN valor_despesas ELSE 0 END) AS valor_ultimo
    FROM despesas_consolidado
    WHERE (ano * 10 + trimestre) IN (SELECT first_p FROM periodos UNION SELECT last_p FROM periodos)
    GROUP BY cnpj, razao_social
    HAVING SUM(CASE WHEN (ano * 10 + trimestre) = (SELECT first_p FROM periodos) THEN valor_despesas ELSE 0 END) > 0
       AND SUM(CASE WHEN (ano * 10 + trimestre) = (SELECT last_p FROM periodos) THEN valor_despesas ELSE 0 END) > 0
)
SELECT razao_social, valor_primeiro, valor_ultimo,
       ROUND(100.0 * (valor_ultimo - valor_primeiro) / NULLIF(valor_primeiro, 0), 2) AS crescimento_pct
FROM primeiro_ultimo
ORDER BY crescimento_pct DESC
LIMIT 5;

-- Query 2: Top 5 UFs por despesa total e media de despesas por operadora em cada UF.
WITH totais_uf AS (
    SELECT uf, SUM(valor_total) AS total_uf, COUNT(*) AS num_operadoras
    FROM despesas_agregadas
    WHERE uf IS NOT NULL AND uf <> ''
    GROUP BY uf
)
SELECT uf, total_uf AS despesa_total,
       ROUND(total_uf / NULLIF(num_operadoras, 0), 2) AS media_por_operadora
FROM totais_uf
ORDER BY total_uf DESC
LIMIT 5;

-- Query 3: Quantidade de operadoras com despesas acima da media geral em pelo menos 2 dos 3 trimestres.
-- Abordagem: CTE com media geral por trimestre; depois por operadora/trimestre flag acima da media; contar operadoras com pelo menos 2 flags.
WITH media_geral_trimestre AS (
    SELECT ano, trimestre, AVG(valor_despesas) AS media_trim
    FROM despesas_consolidado
    GROUP BY ano, trimestre
),
acima_media AS (
    SELECT d.cnpj, d.razao_social, d.ano, d.trimestre,
           CASE WHEN d.valor_despesas > m.media_trim THEN 1 ELSE 0 END AS acima
    FROM despesas_consolidado d
    JOIN media_geral_trimestre m ON d.ano = m.ano AND d.trimestre = m.trimestre
),
contagem AS (
    SELECT cnpj, razao_social, SUM(acima) AS trimestres_acima_media
    FROM acima_media
    GROUP BY cnpj, razao_social
)
SELECT COUNT(*) AS operadoras_acima_media_em_2_ou_3_trimestres
FROM contagem
WHERE trimestres_acima_media >= 2;
