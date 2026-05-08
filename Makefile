.PHONY: install-dev lint test build-dashboard audit openapi smoke-local start-local

PYTHON ?= python3

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"
	cd apps/dashboard-web && npm ci

lint:
	$(PYTHON) -m ruff check src tests alembic

test:
	./ops/tools/run_tests.sh -q

build-dashboard:
	cd apps/dashboard-web && npm run build

audit:
	$(PYTHON) -m pip_audit
	cd apps/dashboard-web && npm audit --omit=dev --audit-level=moderate

openapi:
	$(PYTHON) -m quant_evo_nextgen.runner.export_openapi --output docs/openapi.json

start-local:
	./ops/tools/start_local.sh

smoke-local:
	./ops/tools/smoke_local.sh
