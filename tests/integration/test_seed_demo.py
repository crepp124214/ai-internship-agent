"""Smoke tests for the demo seed script."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "seed_demo.py"
MIGRATE_PATH = REPO_ROOT / "scripts" / "migrate.py"


def _run_seed(database_url: str) -> subprocess.CompletedProcess[str]:
    env = _build_env(database_url)

    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_migrate(database_url: str) -> subprocess.CompletedProcess[str]:
    env = _build_env(database_url)

    return subprocess.run(
        [sys.executable, str(MIGRATE_PATH)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _build_env(database_url: str) -> dict[str, str]:
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    env["LLM_PROVIDER"] = "mock"
    env["SECRET_KEY"] = "seed-demo-test-secret"
    env["APP_DEBUG"] = "False"
    return env


def test_seed_demo_script_is_idempotent():
    with tempfile.TemporaryDirectory() as temp_dir:
        database_url = f"sqlite:///{Path(temp_dir, 'demo.db').as_posix()}"

        migrate_run = _run_migrate(database_url)
        assert migrate_run.returncode == 0, migrate_run.stderr

        first_run = _run_seed(database_url)
        assert first_run.returncode == 0, first_run.stderr
        assert "Demo seed completed." in first_run.stdout
        assert "User: demo / demo123" in first_run.stdout
        assert "Resume ID:" in first_run.stdout
        assert "Job ID:" in first_run.stdout
        assert "Interview Record ID:" in first_run.stdout
        assert "Application ID:" in first_run.stdout

        second_run = _run_seed(database_url)
        assert second_run.returncode == 0, second_run.stderr
        assert "Demo seed completed." in second_run.stdout
        assert "User: demo / demo123" in second_run.stdout
