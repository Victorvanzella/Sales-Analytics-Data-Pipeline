.PHONY: setup generate ingest dbt-run dbt-test pipeline verify test lint docs clean

setup:
	python -m pip install -r requirements-dev.txt

generate:
	python -m src.generate_data

ingest:
	python -m src.ingest

dbt-run:
	dbt run --profiles-dir .

dbt-test:
	dbt test --profiles-dir .

pipeline:
	python -m src.pipeline

verify:
	python -m src.verify_outputs

test:
	pytest

lint:
	ruff check .
	ruff format --check .

docs:
	dbt docs generate --profiles-dir .

clean:
	python -m src.clean_outputs
