from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import Settings, settings

TABLE_NAMES = ("customers", "products", "orders", "order_items")

CATEGORY_CATALOG = {
    "Electronics": ("Smartphones", "Computers", "Audio", "Accessories"),
    "Home": ("Furniture", "Kitchen", "Decoration", "Cleaning"),
    "Sports": ("Running", "Fitness", "Outdoor", "Team Sports"),
    "Books": ("Technology", "Business", "Fiction", "Education"),
    "Beauty": ("Skin Care", "Hair Care", "Fragrance", "Makeup"),
}

LOCATIONS = (
    ("Brazil", "SP", "Sao Paulo"),
    ("Brazil", "RJ", "Rio de Janeiro"),
    ("Brazil", "MG", "Belo Horizonte"),
    ("Brazil", "PR", "Curitiba"),
    ("Brazil", "RS", "Porto Alegre"),
    ("Brazil", "SC", "Florianopolis"),
    ("Brazil", "BA", "Salvador"),
    ("Brazil", "PE", "Recife"),
    ("Argentina", "BA", "Buenos Aires"),
    ("Chile", "RM", "Santiago"),
    ("Colombia", "DC", "Bogota"),
)


@dataclass(frozen=True)
class GeneratedDataset:
    customers: pd.DataFrame
    products: pd.DataFrame
    orders: pd.DataFrame
    order_items: pd.DataFrame

    def as_dict(self) -> dict[str, pd.DataFrame]:
        return {name: getattr(self, name) for name in TABLE_NAMES}


def _date_values(rng: np.random.Generator, start: str, end: str, size: int) -> pd.DatetimeIndex:
    start_date = pd.Timestamp(start)
    day_span = (pd.Timestamp(end) - start_date).days + 1
    return pd.DatetimeIndex(start_date + pd.to_timedelta(rng.integers(0, day_span, size), unit="D"))


def generate_customers(count: int, rng: np.random.Generator) -> pd.DataFrame:
    if count < 10:
        raise ValueError("customer_count deve ser pelo menos 10")
    location_indexes = rng.choice(
        len(LOCATIONS),
        size=count,
        p=[0.24, 0.13, 0.09, 0.08, 0.06, 0.05, 0.05, 0.04, 0.10, 0.08, 0.08],
    )
    locations = [LOCATIONS[index] for index in location_indexes]
    signup_dates = _date_values(rng, "2022-01-01", "2023-12-31", count)
    return pd.DataFrame(
        {
            "customer_id": [f"CUS{index:06d}" for index in range(1, count + 1)],
            "customer_name": [f"Customer {index:06d}" for index in range(1, count + 1)],
            "email": [f"customer{index:06d}@example.com" for index in range(1, count + 1)],
            "segment": rng.choice(
                ["Consumer", "Corporate", "Small Business"],
                size=count,
                p=[0.68, 0.20, 0.12],
            ),
            "city": [location[2] for location in locations],
            "state": [location[1] for location in locations],
            "country": [location[0] for location in locations],
            "signup_date": signup_dates,
            "updated_at": signup_dates + pd.to_timedelta(rng.integers(0, 60, count), unit="D"),
        }
    )


def generate_products(count: int, rng: np.random.Generator) -> pd.DataFrame:
    if count < 10:
        raise ValueError("product_count deve ser pelo menos 10")
    category_names = tuple(CATEGORY_CATALOG)
    categories = [category_names[index % len(category_names)] for index in range(count)]
    subcategories = [
        CATEGORY_CATALOG[category][index % len(CATEGORY_CATALOG[category])]
        for index, category in enumerate(categories)
    ]
    list_prices = np.round(rng.lognormal(mean=5.15, sigma=0.75, size=count), 2)
    list_prices = np.clip(list_prices, 24.90, 4999.90)
    unit_costs = np.round(list_prices * rng.uniform(0.42, 0.72, size=count), 2)
    return pd.DataFrame(
        {
            "product_id": [f"PRD{index:04d}" for index in range(1, count + 1)],
            "product_name": [
                f"{subcategory} Product {index:03d}"
                for index, subcategory in enumerate(subcategories, start=1)
            ],
            "category": categories,
            "subcategory": subcategories,
            "unit_cost": unit_costs,
            "list_price": list_prices,
            "is_active": rng.choice([True, False], size=count, p=[0.96, 0.04]),
            "updated_at": pd.Timestamp("2024-01-01")
            + pd.to_timedelta(rng.integers(0, 365, count), unit="D"),
        }
    )


def generate_orders(count: int, customers: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    if count < 100:
        raise ValueError("order_count deve ser pelo menos 100")
    order_dates = _date_values(rng, "2024-01-01", "2025-12-31", count)
    customer_indexes = rng.integers(0, len(customers), size=count)
    selected_customers = customers.iloc[customer_indexes].reset_index(drop=True)
    return pd.DataFrame(
        {
            "order_id": [f"ORD{index:08d}" for index in range(1, count + 1)],
            "customer_id": selected_customers["customer_id"].to_numpy(),
            "order_date": order_dates,
            "order_status": rng.choice(
                ["Delivered", "Shipped", "Processing", "Cancelled", "Returned"],
                size=count,
                p=[0.78, 0.08, 0.05, 0.07, 0.02],
            ),
            "payment_method": rng.choice(
                ["Credit Card", "Pix", "Boleto", "Digital Wallet"],
                size=count,
                p=[0.45, 0.34, 0.12, 0.09],
            ),
            "sales_channel": rng.choice(
                ["Website", "Mobile App", "Marketplace"],
                size=count,
                p=[0.48, 0.37, 0.15],
            ),
            "shipping_country": selected_customers["country"].to_numpy(),
            "updated_at": order_dates + pd.to_timedelta(rng.integers(0, 4, count), unit="D"),
        }
    )


def generate_order_items(
    orders: pd.DataFrame, products: pd.DataFrame, rng: np.random.Generator
) -> pd.DataFrame:
    items_per_order = rng.choice([1, 2, 3, 4], size=len(orders), p=[0.44, 0.33, 0.17, 0.06])
    order_indexes = np.repeat(np.arange(len(orders)), items_per_order)
    product_indexes = rng.integers(0, len(products), size=len(order_indexes))
    quantities = rng.choice(
        [1, 2, 3, 4, 5], size=len(order_indexes), p=[0.52, 0.26, 0.13, 0.06, 0.03]
    )
    base_prices = products.iloc[product_indexes]["list_price"].to_numpy(dtype=float)
    prices = np.round(base_prices * rng.uniform(0.94, 1.04, len(order_indexes)), 2)
    discounts = rng.choice(
        [0.0, 0.05, 0.10, 0.15, 0.20, 0.30],
        size=len(order_indexes),
        p=[0.40, 0.15, 0.20, 0.11, 0.10, 0.04],
    )
    totals = np.round(quantities * prices * (1 - discounts), 2)
    return pd.DataFrame(
        {
            "order_item_id": [f"ITM{index:09d}" for index in range(1, len(order_indexes) + 1)],
            "order_id": orders.iloc[order_indexes]["order_id"].to_numpy(),
            "product_id": products.iloc[product_indexes]["product_id"].to_numpy(),
            "quantity": quantities,
            "unit_price": prices,
            "discount_pct": discounts,
            "item_total": totals,
            "updated_at": orders.iloc[order_indexes]["updated_at"].to_numpy(),
        }
    )


def generate_dataset(
    customer_count: int, product_count: int, order_count: int, seed: int
) -> GeneratedDataset:
    rng = np.random.default_rng(seed)
    customers = generate_customers(customer_count, rng)
    products = generate_products(product_count, rng)
    orders = generate_orders(order_count, customers, rng)
    order_items = generate_order_items(orders, products, rng)
    return GeneratedDataset(customers, products, orders, order_items)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for block in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_dataset(dataset: GeneratedDataset, config: Settings) -> dict:
    config.ensure_directories()
    files: dict[str, dict[str, str | int]] = {}
    for table_name, dataframe in dataset.as_dict().items():
        destination = config.source_path(table_name)
        temporary = destination.with_suffix(".parquet.tmp")
        dataframe.to_parquet(temporary, index=False, engine="pyarrow")
        temporary.replace(destination)
        files[table_name] = {
            "path": str(destination.relative_to(config.project_root)),
            "rows": len(dataframe),
            "sha256": _sha256(destination),
        }
    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "seed": config.seed,
        "files": files,
    }
    temporary_manifest = config.manifest_path.with_suffix(".json.tmp")
    temporary_manifest.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary_manifest.replace(config.manifest_path)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera fontes normalizadas de vendas em Parquet.")
    parser.add_argument("--customers", type=int, default=settings.customer_count)
    parser.add_argument("--products", type=int, default=settings.product_count)
    parser.add_argument("--orders", type=int, default=settings.order_count)
    parser.add_argument("--seed", type=int, default=settings.seed)
    args = parser.parse_args()
    config = Settings(
        project_root=settings.project_root,
        customer_count=args.customers,
        product_count=args.products,
        order_count=args.orders,
        seed=args.seed,
        dbt_threads=settings.dbt_threads,
    )
    dataset = generate_dataset(args.customers, args.products, args.orders, args.seed)
    manifest = write_dataset(dataset, config)
    counts = ", ".join(f"{name}={details['rows']}" for name, details in manifest["files"].items())
    print(f"Fontes geradas: {counts}.")


if __name__ == "__main__":
    main()
