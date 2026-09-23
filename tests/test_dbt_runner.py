from __future__ import annotations

from types import SimpleNamespace

import pytest

import src.dbt_runner as dbt_runner


def test_run_dbt_passes_environment_and_project_directory(temp_config, monkeypatch) -> None:
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="Done")

    monkeypatch.setattr(dbt_runner.shutil, "which", lambda name: "/tools/dbt")
    monkeypatch.setattr(dbt_runner.subprocess, "run", fake_run)

    result = dbt_runner.run_dbt(temp_config, ["run"])

    assert result.command == "dbt run"
    assert captured["command"] == ["/tools/dbt", "--no-use-colors", "run", "--profiles-dir", "."]
    assert captured["cwd"] == temp_config.project_root
    assert captured["env"]["WAREHOUSE_PATH"] == str(temp_config.warehouse_path)


def test_run_dbt_raises_with_output_tail(temp_config, monkeypatch) -> None:
    monkeypatch.setattr(dbt_runner.shutil, "which", lambda name: "/tools/dbt")
    monkeypatch.setattr(
        dbt_runner.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=2, stdout="SQL compilation failed"),
    )

    with pytest.raises(RuntimeError, match="SQL compilation failed"):
        dbt_runner.run_dbt(temp_config, ["test"])


def test_dbt_pipeline_runs_expected_commands(temp_config, monkeypatch) -> None:
    commands = []

    def fake_dbt(config, arguments):
        commands.append(arguments)
        return dbt_runner.DbtCommandResult("dbt command", 0.1, "ok")

    monkeypatch.setattr(dbt_runner, "run_dbt", fake_dbt)

    results = dbt_runner.run_dbt_pipeline(temp_config, full_refresh=True)

    assert commands == [
        ["source", "freshness"],
        ["build", "--full-refresh"],
    ]
    assert len(results) == 2
