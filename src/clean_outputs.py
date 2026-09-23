from __future__ import annotations

import shutil

from src.config import Settings, settings


def clean_generated_outputs(config: Settings = settings) -> list[str]:
    files = [
        *(config.source_path(name) for name in ("customers", "products", "orders", "order_items")),
        config.manifest_path,
        config.warehouse_path,
        config.warehouse_path.with_suffix(".duckdb.wal"),
        config.metrics_path,
        config.verification_path,
        config.log_path,
        *config.exports_dir.glob("*.csv"),
        *config.exports_dir.glob("*.parquet"),
    ]
    removed: list[str] = []
    for path in files:
        if path.exists() and path.is_file():
            path.unlink()
            removed.append(str(path.relative_to(config.project_root)))

    target_path = config.project_root / "target"
    if target_path.exists() and target_path.is_dir():
        shutil.rmtree(target_path)
        removed.append("target/")
    return removed


def main() -> None:
    removed = clean_generated_outputs()
    print(f"Limpeza concluida: {len(removed)} artefatos removidos.")


if __name__ == "__main__":
    main()
