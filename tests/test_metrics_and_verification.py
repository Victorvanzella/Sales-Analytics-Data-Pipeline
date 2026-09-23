from __future__ import annotations

import json
import logging

import pytest

from src.export_marts import MART_EXPORTS
from src.logging_config import configure_logging
from src.metrics import collect_pipeline_metrics, write_json_atomic
from src.verify_outputs import verify_outputs
from src.warehouse import connect_warehouse


def _build_analytics_warehouse(config) -> None:
    connection = connect_warehouse(config.warehouse_path)
    try:
        connection.execute("CREATE SCHEMA raw")
        connection.execute("CREATE SCHEMA marts")
        connection.execute("CREATE TABLE raw.orders AS SELECT 'ORD1' AS order_id")
        connection.execute("CREATE TABLE raw.order_items AS SELECT 'ITM1' AS order_item_id")
        connection.execute("CREATE TABLE marts.dim_customer AS SELECT 'CUS_SK' AS customer_sk")
        connection.execute(
            "CREATE TABLE marts.dim_product AS "
            "SELECT 'PRD_SK' AS product_sk, 'Electronics' AS category"
        )
        connection.execute("CREATE TABLE marts.dim_date AS SELECT 20250101 AS date_key")
        connection.execute(
            """
            CREATE TABLE marts.fct_sales AS
            SELECT
                'ORD1' AS order_id,
                'CUS_SK' AS customer_sk,
                'PRD_SK' AS product_sk,
                20250101 AS date_key,
                2 AS quantity,
                100.00::DECIMAL(18, 2) AS gross_sales_amount,
                10.00::DECIMAL(18, 2) AS discount_amount,
                90.00::DECIMAL(18, 2) AS recognized_revenue,
                0.00::DECIMAL(18, 2) AS returned_amount,
                30.00::DECIMAL(18, 2) AS margin_amount,
                'Delivered' AS order_status,
                'Website' AS sales_channel
            """
        )
        connection.execute(
            """
            CREATE TABLE marts.mart_daily_sales AS
            SELECT DATE '2025-01-01' AS order_date, 90.00::DECIMAL(18, 2) AS recognized_revenue
            """
        )
    finally:
        connection.close()


def _create_runtime_evidence(config) -> None:
    config.ensure_directories()
    for mart_name in MART_EXPORTS:
        (config.exports_dir / f"{mart_name}.csv").write_text("id\n1\n", encoding="utf-8")
        (config.exports_dir / f"{mart_name}.parquet").write_bytes(b"PAR1-test")
    target = config.project_root / "target"
    target.mkdir(parents=True)
    (target / "run_results.json").write_text(
        json.dumps(
            {
                "results": [
                    {"unique_id": "model.sales_analytics.dim_date", "status": "success"},
                    {"unique_id": "test.sales_analytics.first", "status": "pass"},
                    {"unique_id": "test.sales_analytics.second", "status": "pass"},
                ]
            }
        ),
        encoding="utf-8",
    )


def test_collect_metrics_reads_warehouse_and_dbt_results(temp_config) -> None:
    _build_analytics_warehouse(temp_config)
    _create_runtime_evidence(temp_config)
    generated = {"customers": 1, "products": 1, "orders": 1, "order_items": 1}

    metrics = collect_pipeline_metrics(
        temp_config,
        run_id="run-1",
        duration_seconds=1.2345,
        generated_counts=generated,
        exported_files=[temp_config.exports_dir / "mart_daily_sales.csv"],
        dbt_commands=[{"command": "dbt test", "duration_seconds": 0.5}],
    )

    assert metrics["status"] == "SUCCESS"
    assert metrics["warehouse_rows"]["fct_sales"] == 1
    assert metrics["analytics"]["recognized_revenue"] == 90.0
    assert metrics["analytics"]["top_category"]["name"] == "Electronics"
    assert metrics["dbt"]["test_summary"] == {"total": 2, "passed": 2, "failed": 0}


def test_verify_outputs_approves_consistent_star_schema(temp_config) -> None:
    _build_analytics_warehouse(temp_config)
    _create_runtime_evidence(temp_config)
    metrics = {
        "status": "SUCCESS",
        "generated_rows": {"customers": 1, "products": 1, "orders": 1, "order_items": 1},
        "dbt": {"test_summary": {"failed": 0}},
    }
    write_json_atomic(metrics, temp_config.metrics_path)

    report = verify_outputs(temp_config)

    assert report["status"] == "PASSED"
    assert len(report["checks"]) == 9
    assert all(report["checks"].values())
    assert temp_config.verification_path.exists()


def test_verify_outputs_rejects_missing_artifacts(temp_config) -> None:
    with pytest.raises(FileNotFoundError, match="Saidas obrigatorias ausentes"):
        verify_outputs(temp_config)


def test_verify_outputs_reports_reconciliation_failure(temp_config) -> None:
    _build_analytics_warehouse(temp_config)
    _create_runtime_evidence(temp_config)
    connection = connect_warehouse(temp_config.warehouse_path)
    try:
        connection.execute("UPDATE marts.mart_daily_sales SET recognized_revenue = 80")
    finally:
        connection.close()
    write_json_atomic(
        {
            "status": "SUCCESS",
            "generated_rows": {"customers": 1, "products": 1, "orders": 1},
            "dbt": {"test_summary": {"failed": 0}},
        },
        temp_config.metrics_path,
    )

    with pytest.raises(AssertionError, match="daily_revenue_reconciles"):
        verify_outputs(temp_config)

    report = json.loads(temp_config.verification_path.read_text(encoding="utf-8"))
    assert report["status"] == "FAILED"


def test_logging_writes_pipeline_file(temp_config) -> None:
    configure_logging(temp_config.log_path)
    logging.getLogger("test").info("pipeline test message")
    logging.shutdown()

    assert "pipeline test message" in temp_config.log_path.read_text(encoding="utf-8")
