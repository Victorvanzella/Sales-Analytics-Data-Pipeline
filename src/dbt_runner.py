from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from src.config import Settings

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DbtCommandResult:
    command: str
    duration_seconds: float
    output: str


def _dbt_executable() -> str:
    executable = shutil.which("dbt")
    if executable:
        return executable
    environment_executable = Path(sys.executable).parent / "dbt"
    if environment_executable.exists():
        return str(environment_executable)
    raise FileNotFoundError("Executavel dbt nao encontrado. Instale requirements.txt.")


def run_dbt(config: Settings, arguments: list[str]) -> DbtCommandResult:
    command = [_dbt_executable(), "--no-use-colors", *arguments, "--profiles-dir", "."]
    environment = os.environ.copy()
    environment.update(
        {
            "WAREHOUSE_PATH": str(config.warehouse_path),
            "DBT_PROFILES_DIR": str(config.dbt_profiles_dir),
            "DBT_THREADS": str(config.dbt_threads),
        }
    )
    started_at = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=config.project_root,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    duration = time.perf_counter() - started_at
    command_name = "dbt " + " ".join(arguments)
    LOGGER.info("%s concluido em %.2fs", command_name, duration)
    LOGGER.debug("Saida de %s:\n%s", command_name, completed.stdout)
    if completed.returncode != 0:
        tail = "\n".join(completed.stdout.splitlines()[-40:])
        raise RuntimeError(f"{command_name} falhou com codigo {completed.returncode}:\n{tail}")
    return DbtCommandResult(command_name, round(duration, 3), completed.stdout)


def run_dbt_pipeline(config: Settings, *, full_refresh: bool = False) -> list[DbtCommandResult]:
    results = [run_dbt(config, ["source", "freshness"])]
    run_arguments = ["build"]
    if full_refresh:
        run_arguments.append("--full-refresh")
    results.append(run_dbt(config, run_arguments))
    return results
