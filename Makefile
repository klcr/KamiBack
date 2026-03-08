.PHONY: build test lint typecheck format clean setup-hooks

build:
	@echo "Building domain + api..."
	python -m py_compile domain/src/__init__.py
	@echo "Building web..."
	@if [ -f web/node_modules/.package-lock.json ]; then cd web && npm run build; else echo "web node_modules not installed — skipping web build"; fi

test:
	pytest domain/ api/ -v --import-mode=importlib
	@if [ -f web/node_modules/.package-lock.json ] && find web/src -name '*.test.*' -o -name '*.spec.*' 2>/dev/null | grep -q .; then cd web && npx vitest run; else echo "web tests skipped (no node_modules or no test files)"; fi

lint:
	ruff check domain/ api/
	ruff format --check domain/ api/
	@if [ -f web/node_modules/.package-lock.json ]; then cd web && npx biome check ./src; else echo "web node_modules not installed — skipping web lint"; fi

typecheck:
	mypy domain/src api/src
	@if [ -f web/tsconfig.json ]; then cd web && npx tsc --noEmit; else echo "web/tsconfig.json not found — skipping web typecheck"; fi

format:
	ruff format domain/ api/
	@if [ -f web/node_modules/.package-lock.json ]; then cd web && npx biome format --write ./src; else echo "web node_modules not installed — skipping web format"; fi

setup-hooks:
	git config core.hooksPath .githooks
	@echo "Git hooks configured to use .githooks/"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
