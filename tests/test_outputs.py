from __future__ import annotations

import json

from src.clean_outputs import clean_generated_outputs
from src.export_marts import MART_EXPORTS, export_marts
from src.metrics import write_json_atomic
from src.warehouse import connect_warehouse


def _create_exportable_marts(config) -> None:
    connection = connect_warehouse(config.warehouse_path)
    try:
        connection.execute("CREATE SCHEMA marts")
        for table_name in MART_EXPORTS:
            connection.execute(
                f"CREATE TABLE marts.{table_name} AS SELECT 1 AS record_id, 'ok' AS status"
            )
    finally:
        connection.close()


def test_export_marts_writes_csv_and_parquet(temp_config) -> None:
    _create_exportable_marts(temp_config)

    exported = export_marts(temp_config)

    assert len(exported) == 12
    assert all(path.exists() and path.stat().st_size > 0 for path in exported)


def test_write_json_atomic_replaces_destination(temp_config) -> None:
    write_json_atomic({"status": "first"}, temp_config.metrics_path)
    write_json_atomic({"status": "second"}, temp_config.metrics_path)

    payload = json.loads(temp_config.metrics_path.read_text(encoding="utf-8"))
    assert payload == {"status": "second"}
    assert not temp_config.metrics_path.with_suffix(".json.tmp").exists()


def test_clean_outputs_preserves_unknown_file(temp_config, small_dataset) -> None:
    from src.generate_data import write_dataset

    write_dataset(small_dataset, temp_config)
    _create_exportable_marts(temp_config)
    export_marts(temp_config)
    write_json_atomic({"status": "ok"}, temp_config.metrics_path)
    keep = temp_config.exports_dir / "keep.txt"
    keep.write_text("preserve", encoding="utf-8")
    target = temp_config.project_root / "target"
    target.mkdir()
    (target / "manifest.json").write_text("{}", encoding="utf-8")

    removed = clean_generated_outputs(temp_config)

    assert "target/" in removed
    assert keep.exists()
    assert not temp_config.warehouse_path.exists()
    assert not temp_config.source_path("orders").exists()
