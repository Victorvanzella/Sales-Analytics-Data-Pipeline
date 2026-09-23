from __future__ import annotations

from src.warehouse import (
    connect_warehouse,
    finish_pipeline_run,
    start_pipeline_run,
)


def test_pipeline_audit_lifecycle(temp_config) -> None:
    connection = connect_warehouse(temp_config.warehouse_path)
    try:
        start_pipeline_run(connection, "run-123")
        finish_pipeline_run(
            connection,
            "run-123",
            status="SUCCESS",
            counts={"customers": 20, "products": 10, "orders": 100, "order_items": 180},
        )
        row = connection.execute(
            """
            SELECT status, customer_count, order_count, completed_at IS NOT NULL
            FROM audit.pipeline_runs WHERE run_id = 'run-123'
            """
        ).fetchone()
    finally:
        connection.close()

    assert row == ("SUCCESS", 20, 100, True)
