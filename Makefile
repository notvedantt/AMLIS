.PHONY: setup lint types arch test leakage check
setup:
	python -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]" && pre-commit install
lint:
	ruff check . && ruff format --check .
types:
	mypy
arch:
	lint-imports
test:
	pytest
leakage:
	pytest tests/leakage
check: lint types arch test
