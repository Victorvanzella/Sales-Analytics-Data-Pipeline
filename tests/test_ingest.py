from __future__ import annotations

import json

import pytest

from src.generate_data import write_dataset
from src.ingest import ingest_sources, load_manifest
from src.warehouse import connect_warehouse


def test_ingestion_loads_all_raw_tables(temp_config, small_dataset) -> None:
    write_dataset(small_dataset, temp_config)

    counts = ingest_sources(temp_config, "test-run")

    assert counts["orders"] == 100
    connection = connect_warehouse(temp_config.warehouse_path, read_only=True)
    try:
        assert (
            connection.execute("SELECT COUNT(*) FROM raw.order_items").fetchone()[0]
            == counts["order_items"]
        )
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM raw.orders WHERE _ingested_at IS NULL"
            ).fetchone()[0]
            == 0
        )
        assert connection.execute("SELECT COUNT(*) FROM audit.ingestion_log").fetchone()[0] == 4
    finally:
        connection.close()


def test_load_manifest_rejects_missing_file(temp_config) -> None:
    with pytest.raises(FileNotFoundError, match="Manifesto nao encontrado"):
        load_manifest(temp_config)


def test_load_manifest_rejects_incomplete_payload(temp_config) -> None:
    temp_config.ensure_directories()
    temp_config.manifest_path.write_text(json.dumps({"files": {"orders": {}}}), encoding="utf-8")

    with pytest.raises(ValueError, match="Manifesto incompleto"):
        load_manifest(temp_config)


def test_ingestion_rejects_missing_source_file(temp_config, small_dataset) -> None:
    write_dataset(small_dataset, temp_config)
    temp_config.source_path("orders").unlink()

    with pytest.raises(FileNotFoundError, match="Fonte nao encontrada"):
        ingest_sources(temp_config, "test-run")
