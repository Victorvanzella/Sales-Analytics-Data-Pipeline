# Evidências de execução

O pipeline grava nesta pasta:

- `pipeline_metrics.json`: contagens, duração, resultados dbt e KPIs;
- `verification_report.json`: nove verificações independentes das saídas.

Os relatórios são reproduzíveis e ignorados pelo Git. A CI os disponibiliza como artefatos temporários.
