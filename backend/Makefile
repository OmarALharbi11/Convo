.PHONY: install dev test test-fast lint format clean run-mock setup-logs

install:
	pip install -r requirements.txt

dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-mock:
	APP_ENV=development USE_MOCK_GRAPH=true USE_MOCK_STT=true USE_MOCK_TTS=true \
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest --tb=short -v --cov=app --cov-report=term-missing

test-fast:
	pytest --tb=short -q -x

lint:
	ruff check app/

format:
	ruff format app/

setup-logs:
	mkdir -p logs

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
