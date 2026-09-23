# Dados do pipeline

- `source/`: quatro fontes Parquet e o manifesto com checksums;
- `warehouse/`: arquivo DuckDB com todas as camadas;
- `exports/`: seis marts em CSV e Parquet.

Os artefatos são gerados por `python -m src.pipeline` e ignorados pelo Git.
