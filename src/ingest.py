from __future__ import annotations

import json
from datetime import UTC, datetime

from src.config import Settings, settings
from src.warehouse import connect_warehouse, initialize_audit

EXPECTED_TABLES = ("customers", "products", "orders", "order_items")


def load_manifest(config: Settings) -> dict:
    if not config.manifest_path.exists():
        raise FileNotFoundError(
            f"Manifesto nao encontrado: {config.manifest_path}. Execute a geracao primeiro."
        )
    manifest = json.loads(config.manifest_path.read_text(encoding="utf-8"))
    missing = sorted(set(EXPECTED_TABLES) - set(manifest.get("files", {})))
    if missing:
        raise ValueError(f"Manifesto incompleto; fontes ausentes: {missing}")
    return manifest


def ingest_sources(config: Settings, run_id: str) -> dict[str, int]:
    manifest = load_manifest(config)
    connection = connect_warehouse(config.warehouse_path)
    counts: dict[str, int] = {}
    try:
        initialize_audit(connection)
        connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
        connection.execute("BEGIN TRANSACTION")
        for table_name in EXPECTED_TABLES:
            details = manifest["files"][table_name]
            source_path = config.project_root / details["path"]
            if not source_path.exists():
                raise FileNotFoundError(f"Fonte nao encontrada: {source_path}")
            connection.execute(
                f"""
                CREATE OR REPLACE TABLE raw.{table_name} AS
                SELECT *, current_timestamp AS _ingested_at
                FROM read_parquet(?)
                """,
                [str(source_path)],
            )
            row_count = int(
                connection.execute(f"SELECT COUNT(*) FROM raw.{table_name}").fetchone()[0]
            )
            if row_count != int(details["rows"]):
                raise RuntimeError(
                    f"Contagem divergente em {table_name}: "
                    f"esperado {details['rows']}, obtido {row_count}"
                )
            connection.execute(
                """
                INSERT INTO audit.ingestion_log
                    (run_id, table_name, row_count, source_sha256, ingested_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [run_id, table_name, row_count, details["sha256"], datetime.now(UTC)],
            )
            counts[table_name] = row_count
        connection.execute("COMMIT")
        return counts
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()


def main() -> None:
    counts = ingest_sources(settings, "manual-ingestion")
    print("Ingestao concluida: " + ", ".join(f"{key}={value}" for key, value in counts.items()))


if __name__ == "__main__":
    main()
