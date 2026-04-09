.PHONY: lint test-unit test-integration test-all test-coverage compose-health help

help:
	@echo "AI Internship Agent - Available targets:"
	@echo "  make lint              - Run linting checks"
	@echo "  make test-unit         - Run unit tests"
	@echo "  make test-integration  - Run integration tests"
	@echo "  make test-all          - Run all tests (unit + integration)"
	@echo "  make test-coverage     - Generate coverage report"
	@echo "  make compose-health    - Wait for Docker Compose services"

lint:
	ruff check src/ tests/

test-unit:
	APP_ENV=development python -m pytest tests/unit/ -v --cov=src --cov-report=term-missing --cov-fail-under=80

test-integration:
	APP_ENV=development python -m pytest tests/integration/ -v --cov=src --cov-report=term-missing

test-all:
	APP_ENV=development python -m pytest tests/unit tests/integration -v --cov=src --cov-report=term-missing --cov-fail-under=80

test-coverage:
	APP_ENV=development python -m pytest tests/unit tests/integration --cov=src --cov-report=html:htmlcov --cov-report=xml:coverage.xml

compose-health:
	./scripts/compose-health.sh
