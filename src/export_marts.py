from __future__ import annotations

from pathlib import Path

from src.config import Settings
from src.warehouse import connect_warehouse

MART_EXPORTS = (
    "mart_daily_sales",
    "mart_monthly_sales",
    "mart_category_performance",
    "mart_customer_360",
    "mart_channel_performance",
    "mart_country_performance",
)


def _sql_path(path: Path) -> str:
    return str(path).replace("'", "''")


def export_marts(config: Settings) -> list[Path]:
    config.exports_dir.mkdir(parents=True, exist_ok=True)
    connection = connect_warehouse(config.warehouse_path, read_only=True)
    exported: list[Path] = []
    try:
        for table_name in MART_EXPORTS:
            csv_path = config.exports_dir / f"{table_name}.csv"
            parquet_path = config.exports_dir / f"{table_name}.parquet"
            connection.execute(
                f"""
                COPY (SELECT * FROM marts.{table_name})
                TO '{_sql_path(csv_path)}' (FORMAT CSV, HEADER TRUE)
                """
            )
            connection.execute(
                f"""
                COPY (SELECT * FROM marts.{table_name})
                TO '{_sql_path(parquet_path)}' (FORMAT PARQUET, COMPRESSION ZSTD)
                """
            )
            exported.extend([csv_path, parquet_path])
    finally:
        connection.close()
    return exported
