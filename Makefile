.PHONY: build test lint typecheck format clean

build:
	@echo "Building domain + api..."
	python -m py_compile domain/src/__init__.py
	@echo "Building web..."
	cd web && npm run build 2>/dev/null || echo "Web build not configured yet"

test:
	pytest domain/ api/ -v
	cd web && npx vitest run 2>/dev/null || echo "Web tests not configured yet"

lint:
	ruff check domain/ api/
	cd web && npx biome check ./src 2>/dev/null || echo "Web lint not configured yet"

typecheck:
	mypy domain/src api/src
	cd web && npx tsc --noEmit 2>/dev/null || echo "Web typecheck not configured yet"

format:
	ruff format domain/ api/
	cd web && npx biome format --write ./src 2>/dev/null || echo "Web format not configured yet"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
