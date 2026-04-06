#!/bin/bash
set -e

echo "Running database migrations..."
python scripts/migrate.py

if [ "${SEED_DEMO_ON_BOOT:-false}" = "true" ]; then
  echo "Seeding demo data..."
  python scripts/seed_demo.py
fi

echo "Starting application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
