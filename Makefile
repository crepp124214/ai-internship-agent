.PHONY: help install install-dev format lint test test-unit test-integration test-e2e run dev migrate seed-demo compose-up compose-down clean

PYTHON ?= python
PYTEST ?= $(PYTHON) -m pytest
UVICORN ?= $(PYTHON) -m uvicorn

help:
	@echo "AI Internship Agent - command entrypoint"
	@echo ""
	@echo "Available targets:"
	@echo "  make install            Install runtime dependencies"
	@echo "  make install-dev        Install runtime and development dependencies"
	@echo "  make format             Run black and isort"
	@echo "  make lint               Run flake8, mypy, black --check, isort --check"
	@echo "  make test               Run the default pytest suite"
	@echo "  make test-unit          Run unit tests only"
	@echo "  make test-integration   Run integration tests only"
	@echo "  make test-e2e           Run end-to-end tests only"
	@echo "  make run                Run the FastAPI app"
	@echo "  make dev                Run the FastAPI app with reload"
	@echo "  make migrate            Run Alembic migrations to head"
	@echo "  make seed-demo          Seed one local portfolio demo dataset"
	@echo "  make compose-up         Start the release-like docker compose stack"
	@echo "  make compose-down       Stop the docker compose stack"
	@echo "  make clean              Remove local Python cache and test artifacts"

install:
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install
	$(PYTHON) -m pip install -r requirements-dev.txt

format:
	$(PYTHON) -m black src tests
	$(PYTHON) -m isort src tests

lint:
	$(PYTHON) -m flake8 src tests
	$(PYTHON) -m mypy src
	$(PYTHON) -m black --check src tests
	$(PYTHON) -m isort --check-only src tests

test:
	$(PYTEST)

test-unit:
	$(PYTEST) tests/unit

test-integration:
	$(PYTEST) tests/integration

test-e2e:
	$(PYTEST) tests/e2e

run:
	$(PYTHON) src/main.py

dev:
	$(UVICORN) src.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	$(PYTHON) scripts/migrate.py

seed-demo:
	$(PYTHON) scripts/seed_demo.py

compose-up:
	docker compose -f docker/docker-compose.yml up --build

compose-down:
	docker compose -f docker/docker-compose.yml down

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc') if p.exists()]; [p.unlink() for p in pathlib.Path('.').rglob('*.pyo') if p.exists()]; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path('.pytest_cache'), pathlib.Path('htmlcov')] if p.exists()]; [p.unlink() for p in [pathlib.Path('.coverage'), pathlib.Path('coverage.xml')] if p.exists()]"
