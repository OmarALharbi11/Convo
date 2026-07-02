.PHONY: dev dev-backend dev-frontend install test docker-up docker-down seed

# Start both backend and frontend (requires two terminals)
dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# Install all dependencies
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Run full test suite
test:
	cd backend && pytest -v --tb=short

# Run tests with coverage
test-cov:
	cd backend && pytest --cov=app --cov-report=html --cov-report=term-missing

# Lint backend
lint:
	cd backend && ruff check app tests

# Docker
docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# Seed mock data 
setup:
	cp backend/.env.example backend/.env
	@echo "Backend .env created. Edit backend/.env to configure Azure credentials."
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals."
