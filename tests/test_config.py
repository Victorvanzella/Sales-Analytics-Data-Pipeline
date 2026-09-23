from __future__ import annotations

from src.config import Settings


def test_settings_build_expected_paths(tmp_path) -> None:
    config = Settings(project_root=tmp_path)

    assert config.warehouse_path == tmp_path / "data/warehouse/sales_analytics.duckdb"
    assert config.source_path("orders") == tmp_path / "data/source/orders.parquet"
    assert config.metrics_path == tmp_path / "reports/pipeline_metrics.json"


def test_ensure_directories_creates_runtime_folders(tmp_path) -> None:
    config = Settings(project_root=tmp_path)

    config.ensure_directories()

    assert config.source_dir.is_dir()
    assert config.warehouse_path.parent.is_dir()
    assert config.exports_dir.is_dir()
    assert config.reports_dir.is_dir()
