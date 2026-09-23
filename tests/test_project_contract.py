from __future__ import annotations

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dbt_project_declares_all_model_layers() -> None:
    project = yaml.safe_load((PROJECT_ROOT / "dbt_project.yml").read_text(encoding="utf-8"))
    model_config = project["models"]["sales_analytics"]

    assert project["profile"] == "sales_analytics"
    assert set(model_config) == {"staging", "intermediate", "marts"}
    assert project["test-paths"] == ["dbt_tests"]


def test_star_schema_and_singular_tests_are_versioned() -> None:
    mart_models = {path.stem for path in (PROJECT_ROOT / "models" / "marts").glob("*.sql")}
    singular_tests = list((PROJECT_ROOT / "dbt_tests").glob("*.sql"))

    assert {"dim_customer", "dim_product", "dim_date", "fct_sales"}.issubset(mart_models)
    assert len(mart_models) == 10
    assert len(singular_tests) == 5


def test_incremental_fact_has_unique_key() -> None:
    fact_sql = (PROJECT_ROOT / "models" / "marts" / "fct_sales.sql").read_text(encoding="utf-8")

    assert "materialized='incremental'" in fact_sql
    assert "unique_key='order_item_id'" in fact_sql
    assert "is_incremental()" in fact_sql
