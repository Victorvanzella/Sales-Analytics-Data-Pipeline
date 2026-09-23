# Runbook operacional

## Primeira execução

```bash
python -m src.pipeline --full-refresh
python -m src.verify_outputs
```

Critérios de sucesso:

- processo retorna código `0`;
- `pipeline_metrics.json` apresenta `SUCCESS`;
- 73 testes dbt passam;
- nove verificações finais passam;
- os 12 arquivos de exportação existem.

## Configuração

Copie `.env.example` para `.env` quando precisar alterar os padrões.

| Variável | Padrão | Uso |
|---|---:|---|
| `SALES_CUSTOMER_COUNT` | 5000 | clientes gerados |
| `SALES_PRODUCT_COUNT` | 100 | produtos gerados |
| `SALES_ORDER_COUNT` | 50000 | pedidos gerados |
| `SALES_SEED` | 42 | reprodutibilidade |
| `DBT_THREADS` | 1 | concorrência do dbt local |

## Carga incremental

Depois da carga inicial, execute sem `--full-refresh`. O dbt usa `source_updated_at` e `order_item_id` para processar registros novos ou atualizados. Ao mudar regras históricas, reconstruir dimensões ou remover registros da origem, utilize `--full-refresh`.

## Diagnóstico

| Sintoma | Onde verificar | Ação |
|---|---|---|
| fonte ausente | `data/source/manifest.json` | executar novamente a geração/pipeline |
| checksum ou contagem divergente | `audit.ingestion_log` | validar arquivo Parquet de origem |
| source stale | saída de `dbt source freshness` | verificar a ingestão e `_ingested_at` |
| modelo falhou | `logs/dbt.log` e `target/run_results.json` | corrigir SQL ou schema upstream |
| teste falhou | `target/run_results.json` | abrir SQL compilado em `target/compiled` |
| reconciliação falhou | `verification_report.json` | comparar fato e mart indicado |
| warehouse bloqueado | processos Python/dbt ativos | encerrar o processo que mantém o arquivo aberto |

## Consultar o warehouse

```bash
duckdb data/warehouse/sales_analytics.duckdb
```

Exemplo SQL:

```sql
select *
from marts.mart_monthly_sales
order by month_start;
```

Também é possível conectar Power BI, DBeaver ou um notebook ao arquivo DuckDB, ou utilizar os exports em `data/exports`.

## Limpeza segura

```bash
python -m src.clean_outputs
```

O comando remove somente arquivos e diretórios reproduzíveis conhecidos. Arquivos adicionais criados pelo usuário são preservados.
