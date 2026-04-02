#!/usr/bin/env python3
"""Run database migrations for the project."""

from __future__ import annotations

import argparse
import subprocess
import sys


def run_alembic_upgrade() -> None:
    """Upgrade the database schema to the latest revision."""
    command = [sys.executable, "-m", "alembic", "upgrade", "head"]
    subprocess.run(command, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run database migrations for AI Internship Agent.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables before migrating. Intended for local development only.",
    )
    args = parser.parse_args()

    if args.reset:
        from src.data_access.database import reset_db

        print("Resetting database tables before migration...")
        reset_db()

    print("Running Alembic migrations...")
    try:
        run_alembic_upgrade()
    except subprocess.CalledProcessError as exc:
        print(f"Migration failed with exit code {exc.returncode}.", file=sys.stderr)
        raise SystemExit(exc.returncode) from exc

    print("Database schema is now at head.")


if __name__ == "__main__":
    main()
