from __future__ import annotations

import json
from datetime import UTC, datetime

from src.config import Settings, settings
from src.export_marts import MART_EXPORTS
from src.metrics import write_json_atomic
from src.warehouse import connect_warehouse


def verify_outputs(config: Settings = settings) -> dict:
    required_paths = [
        config.warehouse_path,
        config.metrics_path,
        *(config.exports_dir / f"{name}.parquet" for name in MART_EXPORTS),
        *(config.exports_dir / f"{name}.csv" for name in MART_EXPORTS),
    ]
    missing_paths = [str(path) for path in required_paths if not path.exists()]
    if missing_paths:
        raise FileNotFoundError(f"Saidas obrigatorias ausentes: {missing_paths}")

    metrics = json.loads(config.metrics_path.read_text(encoding="utf-8"))
    connection = connect_warehouse(config.warehouse_path, read_only=True)
    try:
        raw_orders = int(connection.execute("SELECT COUNT(*) FROM raw.orders").fetchone()[0])
        raw_items = int(connection.execute("SELECT COUNT(*) FROM raw.order_items").fetchone()[0])
        fact_rows = int(connection.execute("SELECT COUNT(*) FROM marts.fct_sales").fetchone()[0])
        customer_rows = int(
            connection.execute("SELECT COUNT(*) FROM marts.dim_customer").fetchone()[0]
        )
        product_rows = int(
            connection.execute("SELECT COUNT(*) FROM marts.dim_product").fetchone()[0]
        )
        orphan_keys = int(
            connection.execute(
                """
                SELECT COUNT(*)
                FROM marts.fct_sales AS sales
                LEFT JOIN marts.dim_customer AS customer USING (customer_sk)
                LEFT JOIN marts.dim_product AS product USING (product_sk)
                LEFT JOIN marts.dim_date AS dates USING (date_key)
                WHERE customer.customer_sk IS NULL
                   OR product.product_sk IS NULL
                   OR dates.date_key IS NULL
                """
            ).fetchone()[0]
        )
        revenue_difference = float(
            connection.execute(
                """
                SELECT ABS(
                    (SELECT SUM(recognized_revenue) FROM marts.fct_sales)
                    - (SELECT SUM(recognized_revenue) FROM marts.mart_daily_sales)
                )
                """
            ).fetchone()[0]
        )
        failed_dbt_tests = metrics["dbt"]["test_summary"]["failed"]
        checks = {
            "pipeline_status_success": metrics["status"] == "SUCCESS",
            "raw_orders_match_generation": raw_orders == metrics["generated_rows"]["orders"],
            "fact_matches_item_grain": fact_rows == raw_items,
            "customer_dimension_matches_source": customer_rows
            == metrics["generated_rows"]["customers"],
            "product_dimension_matches_source": product_rows
            == metrics["generated_rows"]["products"],
            "star_schema_has_no_orphans": orphan_keys == 0,
            "daily_revenue_reconciles": revenue_difference <= 0.02,
            "all_dbt_tests_passed": failed_dbt_tests == 0,
            "all_exports_exist": all(path.exists() for path in required_paths[2:]),
        }
    finally:
        connection.close()

    failed_checks = [name for name, passed in checks.items() if not passed]
    report = {
        "verified_at_utc": datetime.now(UTC).isoformat(),
        "status": "PASSED" if not failed_checks else "FAILED",
        "checks": checks,
        "failed_checks": failed_checks,
    }
    write_json_atomic(report, config.verification_path)
    if failed_checks:
        raise AssertionError(f"Verificacao falhou: {failed_checks}")
    return report


def main() -> None:
    result = verify_outputs()
    print(f"Verificacao concluida: {len(result['checks'])} checks aprovados.")


if __name__ == "__main__":
    main()
