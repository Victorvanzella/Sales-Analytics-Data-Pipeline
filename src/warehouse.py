from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import duckdb


def connect_warehouse(path: Path, *, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path), read_only=read_only)


def initialize_audit(connection: duckdb.DuckDBPyConnection) -> None:
    connection.execute("CREATE SCHEMA IF NOT EXISTS audit")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
            run_id VARCHAR PRIMARY KEY,
            started_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ,
            status VARCHAR NOT NULL,
            customer_count BIGINT,
            product_count BIGINT,
            order_count BIGINT,
            order_item_count BIGINT,
            error_message VARCHAR
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS audit.ingestion_log (
            run_id VARCHAR NOT NULL,
            table_name VARCHAR NOT NULL,
            row_count BIGINT NOT NULL,
            source_sha256 VARCHAR NOT NULL,
            ingested_at TIMESTAMPTZ NOT NULL
        )
        """
    )


def start_pipeline_run(connection: duckdb.DuckDBPyConnection, run_id: str) -> None:
    initialize_audit(connection)
    connection.execute(
        "INSERT INTO audit.pipeline_runs (run_id, started_at, status) VALUES (?, ?, ?)",
        [run_id, datetime.now(UTC), "RUNNING"],
    )


def finish_pipeline_run(
    connection: duckdb.DuckDBPyConnection,
    run_id: str,
    *,
    status: str,
    counts: dict[str, int] | None = None,
    error_message: str | None = None,
) -> None:
    counts = counts or {}
    connection.execute(
        """
        UPDATE audit.pipeline_runs
        SET completed_at = ?, status = ?, customer_count = ?, product_count = ?,
            order_count = ?, order_item_count = ?, error_message = ?
        WHERE run_id = ?
        """,
        [
            datetime.now(UTC),
            status,
            counts.get("customers"),
            counts.get("products"),
            counts.get("orders"),
            counts.get("order_items"),
            error_message,
            run_id,
        ],
    )
