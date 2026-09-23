from __future__ import annotations

import argparse
import logging
import time
from datetime import UTC, datetime
from uuid import uuid4

from src.config import Settings, settings
from src.dbt_runner import run_dbt_pipeline
from src.export_marts import export_marts
from src.generate_data import generate_dataset, write_dataset
from src.ingest import ingest_sources
from src.logging_config import configure_logging
from src.metrics import collect_pipeline_metrics, write_json_atomic
from src.verify_outputs import verify_outputs
from src.warehouse import (
    connect_warehouse,
    finish_pipeline_run,
    start_pipeline_run,
)

LOGGER = logging.getLogger(__name__)


def _record_finish(
    config: Settings,
    run_id: str,
    status: str,
    counts: dict[str, int] | None = None,
    error_message: str | None = None,
) -> None:
    connection = connect_warehouse(config.warehouse_path)
    try:
        finish_pipeline_run(
            connection,
            run_id,
            status=status,
            counts=counts,
            error_message=error_message,
        )
    finally:
        connection.close()


def run_pipeline(config: Settings = settings, *, full_refresh: bool = False) -> dict:
    config.ensure_directories()
    configure_logging(config.log_path)
    run_id = uuid4().hex
    started_at = time.perf_counter()
    generated_counts: dict[str, int] = {}

    connection = connect_warehouse(config.warehouse_path)
    try:
        start_pipeline_run(connection, run_id)
    finally:
        connection.close()

    LOGGER.info("run_id=%s pipeline iniciada", run_id)
    try:
        dataset = generate_dataset(
            config.customer_count,
            config.product_count,
            config.order_count,
            config.seed,
        )
        manifest = write_dataset(dataset, config)
        generated_counts = {
            name: int(details["rows"]) for name, details in manifest["files"].items()
        }
        LOGGER.info("fontes Parquet geradas: %s", generated_counts)

        ingested_counts = ingest_sources(config, run_id)
        LOGGER.info("camada raw carregada no DuckDB: %s", ingested_counts)

        dbt_results = run_dbt_pipeline(config, full_refresh=full_refresh)
        exported_files = export_marts(config)
        metrics = collect_pipeline_metrics(
            config,
            run_id=run_id,
            duration_seconds=time.perf_counter() - started_at,
            generated_counts=generated_counts,
            exported_files=exported_files,
            dbt_commands=[
                {"command": result.command, "duration_seconds": result.duration_seconds}
                for result in dbt_results
            ],
        )
        write_json_atomic(metrics, config.metrics_path)
        verify_outputs(config)
        _record_finish(config, run_id, "SUCCESS", generated_counts)
        LOGGER.info("run_id=%s pipeline concluida com sucesso", run_id)
        return metrics
    except Exception as error:
        failure_metrics = {
            "run_id": run_id,
            "status": "FAILED",
            "finished_at_utc": datetime.now(UTC).isoformat(),
            "duration_seconds": round(time.perf_counter() - started_at, 3),
            "generated_rows": generated_counts,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        write_json_atomic(failure_metrics, config.metrics_path)
        try:
            _record_finish(config, run_id, "FAILED", generated_counts, str(error))
        except Exception:
            LOGGER.exception("run_id=%s nao foi possivel atualizar a tabela de auditoria", run_id)
        LOGGER.exception("run_id=%s pipeline interrompida", run_id)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Executa o pipeline completo de Sales Analytics.")
    parser.add_argument("--customers", type=int, default=settings.customer_count)
    parser.add_argument("--products", type=int, default=settings.product_count)
    parser.add_argument("--orders", type=int, default=settings.order_count)
    parser.add_argument("--seed", type=int, default=settings.seed)
    parser.add_argument("--full-refresh", action="store_true")
    args = parser.parse_args()
    config = Settings(
        project_root=settings.project_root,
        customer_count=args.customers,
        product_count=args.products,
        order_count=args.orders,
        seed=args.seed,
        dbt_threads=settings.dbt_threads,
    )
    metrics = run_pipeline(config, full_refresh=args.full_refresh)
    print(
        "Pipeline concluida: "
        f"{metrics['analytics']['orders']} pedidos, "
        f"{metrics['warehouse_rows']['fct_sales']} itens e "
        f"{metrics['dbt']['test_summary']['passed']} testes dbt aprovados."
    )


if __name__ == "__main__":
    main()
