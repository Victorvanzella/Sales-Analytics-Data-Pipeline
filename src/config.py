from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    customer_count: int = int(os.getenv("SALES_CUSTOMER_COUNT", "5000"))
    product_count: int = int(os.getenv("SALES_PRODUCT_COUNT", "100"))
    order_count: int = int(os.getenv("SALES_ORDER_COUNT", "50000"))
    seed: int = int(os.getenv("SALES_SEED", "42"))
    dbt_threads: int = int(os.getenv("DBT_THREADS", "1"))

    @property
    def source_dir(self) -> Path:
        return self.project_root / "data" / "source"

    @property
    def warehouse_path(self) -> Path:
        return self.project_root / "data" / "warehouse" / "sales_analytics.duckdb"

    @property
    def exports_dir(self) -> Path:
        return self.project_root / "data" / "exports"

    @property
    def reports_dir(self) -> Path:
        return self.project_root / "reports"

    @property
    def metrics_path(self) -> Path:
        return self.reports_dir / "pipeline_metrics.json"

    @property
    def verification_path(self) -> Path:
        return self.reports_dir / "verification_report.json"

    @property
    def log_path(self) -> Path:
        return self.project_root / "logs" / "pipeline.log"

    @property
    def manifest_path(self) -> Path:
        return self.source_dir / "manifest.json"

    @property
    def dbt_profiles_dir(self) -> Path:
        return self.project_root

    def source_path(self, table_name: str) -> Path:
        return self.source_dir / f"{table_name}.parquet"

    def ensure_directories(self) -> None:
        for directory in (
            self.source_dir,
            self.warehouse_path.parent,
            self.exports_dir,
            self.reports_dir,
            self.log_path.parent,
        ):
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
