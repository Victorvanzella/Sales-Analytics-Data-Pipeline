from __future__ import annotations

import json

import pandas as pd
import pytest

from src.generate_data import (
    generate_customers,
    generate_dataset,
    generate_orders,
    generate_products,
    write_dataset,
)


def test_generation_is_deterministic() -> None:
    first = generate_dataset(20, 10, 100, 42)
    second = generate_dataset(20, 10, 100, 42)

    for table_name, dataframe in first.as_dict().items():
        pd.testing.assert_frame_equal(dataframe, second.as_dict()[table_name])


def test_generated_counts_and_primary_keys(small_dataset) -> None:
    assert len(small_dataset.customers) == 20
    assert len(small_dataset.products) == 10
    assert len(small_dataset.orders) == 100
    assert len(small_dataset.order_items) >= 100
    assert small_dataset.customers["customer_id"].is_unique
    assert small_dataset.products["product_id"].is_unique
    assert small_dataset.orders["order_id"].is_unique
    assert small_dataset.order_items["order_item_id"].is_unique


def test_generated_foreign_keys_are_valid(small_dataset) -> None:
    assert set(small_dataset.orders["customer_id"]).issubset(
        set(small_dataset.customers["customer_id"])
    )
    assert set(small_dataset.order_items["order_id"]).issubset(
        set(small_dataset.orders["order_id"])
    )
    assert set(small_dataset.order_items["product_id"]).issubset(
        set(small_dataset.products["product_id"])
    )


def test_item_totals_reconcile(small_dataset) -> None:
    items = small_dataset.order_items
    expected = (items["quantity"] * items["unit_price"] * (1 - items["discount_pct"])).round(2)

    pd.testing.assert_series_equal(items["item_total"], expected, check_names=False)


def test_generated_business_domains(small_dataset) -> None:
    assert set(small_dataset.orders["order_status"]).issubset(
        {"Delivered", "Shipped", "Processing", "Cancelled", "Returned"}
    )
    assert small_dataset.customers["email"].str.endswith("@example.com").all()
    assert small_dataset.products["list_price"].gt(0).all()
    assert small_dataset.products["unit_cost"].lt(small_dataset.products["list_price"]).all()


def test_minimum_generation_sizes_are_enforced() -> None:
    rng = __import__("numpy").random.default_rng(42)
    with pytest.raises(ValueError, match="customer_count"):
        generate_customers(9, rng)
    with pytest.raises(ValueError, match="product_count"):
        generate_products(9, rng)
    customers = generate_customers(10, rng)
    with pytest.raises(ValueError, match="order_count"):
        generate_orders(99, customers, rng)


def test_write_dataset_creates_parquet_manifest(temp_config, small_dataset) -> None:
    manifest = write_dataset(small_dataset, temp_config)

    saved_manifest = json.loads(temp_config.manifest_path.read_text(encoding="utf-8"))
    assert manifest == saved_manifest
    assert set(saved_manifest["files"]) == {"customers", "products", "orders", "order_items"}
    assert len(saved_manifest["files"]["orders"]["sha256"]) == 64
    assert pd.read_parquet(temp_config.source_path("orders")).shape[0] == 100
