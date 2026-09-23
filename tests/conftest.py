from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Settings
from src.generate_data import GeneratedDataset, generate_dataset


@pytest.fixture
def temp_config(tmp_path: Path) -> Settings:
    return Settings(
        project_root=tmp_path,
        customer_count=20,
        product_count=10,
        order_count=100,
        seed=42,
        dbt_threads=1,
    )


@pytest.fixture
def small_dataset(temp_config: Settings) -> GeneratedDataset:
    return generate_dataset(
        temp_config.customer_count,
        temp_config.product_count,
        temp_config.order_count,
        temp_config.seed,
    )
