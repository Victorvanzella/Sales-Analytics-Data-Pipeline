# Arquitetura e decisões técnicas

## Objetivo

Disponibilizar um warehouse analítico reproduzível para vendas, separando responsabilidades de geração, ingestão, transformação, validação e consumo.

## Componentes

| Componente | Responsabilidade |
|---|---|
| Python | gerar fontes, manifestar checksums, ingerir, orquestrar e verificar |
| Parquet | landing tipada e compactada das quatro fontes |
| DuckDB | armazenar raw, auditoria, snapshots e modelos analíticos |
| dbt | transformar, documentar, testar e produzir lineage |
| CSV/Parquet | interface de consumo dos marts |
| GitHub Actions | reproduzir testes e pipeline em ambiente limpo |

## Sequência de execução

1. A configuração é carregada de argumentos, ambiente e padrões seguros.
2. O `run_id` é registrado em `audit.pipeline_runs`.
3. Quatro DataFrames determinísticos são gravados em Parquet.
4. Um manifesto registra seed, contagens e SHA-256 de cada fonte.
5. A ingestão transacional publica as tabelas no schema `raw`.
6. O dbt carrega a seed, verifica freshness e atualiza o snapshot.
7. Staging e intermediate preparam os dados.
8. Dimensões, fato e marts são construídos.
9. Os testes dbt precisam passar antes da publicação.
10. Os seis marts são exportados em CSV e Parquet/ZSTD.
11. Métricas e nove verificações reconciliam as saídas.
12. A auditoria recebe o status final; erros também são persistidos.

## Organização dos schemas

- `raw`: representação das fontes e `_ingested_at`;
- `audit`: execução e ingestão por tabela;
- `staging`: views com tipos e nomes canônicos;
- `intermediate`: regras financeiras e joins reutilizáveis;
- `marts`: Star Schema e tabelas de consumo;
- `reference`: metas carregadas por dbt seed;
- `snapshots`: histórico SCD Tipo 2 de clientes.

## Idempotência

A mesma seed e os mesmos volumes produzem fontes idênticas. A ingestão substitui a fotografia raw da demonstração. A fato utiliza chave única e watermark de atualização; `--full-refresh` permite reconstrução completa quando necessário.

## Tratamento de falhas

Qualquer falha de geração, ingestão, dbt ou verificação encerra o processo com código diferente de zero. `pipeline_metrics.json`, `pipeline.log` e `audit.pipeline_runs` registram o erro sempre que o warehouse permanece acessível.

## Concorrência

O perfil local usa uma thread dbt. Para este volume, o ganho de estabilidade ao compartilhar um único arquivo DuckDB supera o benefício de concorrência. Warehouses cliente-servidor podem aumentar `DBT_THREADS` conforme seus recursos.
