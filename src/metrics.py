from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from src.config import Settings
from src.warehouse import connect_warehouse


def write_json_atomic(payload: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    return path


def _number(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _dbt_test_summary(project_root: Path) -> dict[str, int]:
    run_results_path = project_root / "target" / "run_results.json"
    if not run_results_path.exists():
        return {"total": 0, "passed": 0, "failed": 0}
    payload = json.loads(run_results_path.read_text(encoding="utf-8"))
    results = [
        result
        for result in payload.get("results", [])
        if str(result.get("unique_id", "")).startswith("test.")
    ]
    passed = sum(result.get("status") == "pass" for result in results)
    return {"total": len(results), "passed": passed, "failed": len(results) - passed}


def collect_pipeline_metrics(
    config: Settings,
    *,
    run_id: str,
    duration_seconds: float,
    generated_counts: dict[str, int],
    exported_files: list[Path],
    dbt_commands: list[dict],
) -> dict:
    connection = connect_warehouse(config.warehouse_path, read_only=True)
    try:
        warehouse_counts = {
            "dim_customer": int(
                connection.execute("SELECT COUNT(*) FROM marts.dim_customer").fetchone()[0]
            ),
            "dim_product": int(
                connection.execute("SELECT COUNT(*) FROM marts.dim_product").fetchone()[0]
            ),
            "dim_date": int(
                connection.execute("SELECT COUNT(*) FROM marts.dim_date").fetchone()[0]
            ),
            "fct_sales": int(
                connection.execute("SELECT COUNT(*) FROM marts.fct_sales").fetchone()[0]
            ),
        }
        kpis = connection.execute(
            """
            SELECT
                COUNT(DISTINCT order_id) AS orders,
                COUNT(DISTINCT customer_sk) AS active_customers,
                SUM(quantity) AS units,
                ROUND(SUM(gross_sales_amount), 2) AS gross_sales,
                ROUND(SUM(discount_amount), 2) AS discounts,
                ROUND(SUM(recognized_revenue), 2) AS recognized_revenue,
                ROUND(SUM(returned_amount), 2) AS returned_amount,
                ROUND(SUM(margin_amount) FILTER (WHERE order_status = 'Delivered'), 2)
                    AS recognized_margin
            FROM marts.fct_sales
            """
        ).fetchone()
        top_category = connection.execute(
            """
            SELECT category, ROUND(SUM(recognized_revenue), 2) AS revenue
            FROM marts.fct_sales AS sales
            INNER JOIN marts.dim_product AS product USING (product_sk)
            GROUP BY category
            ORDER BY revenue DESC
            LIMIT 1
            """
        ).fetchone()
        top_channel = connection.execute(
            """
            SELECT sales_channel, ROUND(SUM(recognized_revenue), 2) AS revenue
            FROM marts.fct_sales
            GROUP BY sales_channel
            ORDER BY revenue DESC
            LIMIT 1
            """
        ).fetchone()
        model_count = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.tables
                WHERE table_schema IN ('staging', 'intermediate', 'marts', 'snapshots')
                """
            ).fetchone()[0]
        )
    finally:
        connection.close()

    return {
        "run_id": run_id,
        "status": "SUCCESS",
        "finished_at_utc": datetime.now(UTC).isoformat(),
        "duration_seconds": round(duration_seconds, 3),
        "generated_rows": generated_counts,
        "warehouse_rows": warehouse_counts,
        "analytics": {
            "orders": int(kpis[0]),
            "active_customers": int(kpis[1]),
            "units": int(kpis[2]),
            "gross_sales": _number(kpis[3]),
            "discounts": _number(kpis[4]),
            "recognized_revenue": _number(kpis[5]),
            "returned_amount": _number(kpis[6]),
            "recognized_margin": _number(kpis[7]),
            "top_category": {
                "name": top_category[0],
                "recognized_revenue": _number(top_category[1]),
            },
            "top_channel": {"name": top_channel[0], "recognized_revenue": _number(top_channel[1])},
        },
        "dbt": {
            "models_and_snapshots": model_count,
            "test_summary": _dbt_test_summary(config.project_root),
            "commands": dbt_commands,
        },
        "exports": [str(path.relative_to(config.project_root)) for path in exported_files],
    }
