# Makefile for Knowledge Base Docker operations

.PHONY: help build up down restart logs logs-backend logs-frontend ps shell-backend shell-frontend clean rebuild

# Default target
help:
	@echo "Knowledge Base - Docker Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make build          Build all Docker images"
	@echo "  make up             Start all services"
	@echo "  make down           Stop all services"
	@echo "  make restart        Restart all services"
	@echo "  make logs           View logs from all services"
	@echo "  make logs-backend   View backend logs"
	@echo "  make logs-frontend  View frontend logs"
	@echo "  make ps             Show running containers"
	@echo "  make shell-backend  Open shell in backend container"
	@echo "  make shell-frontend Open shell in frontend container"
	@echo "  make clean          Stop and remove containers, volumes"
	@echo "  make rebuild        Clean rebuild of all services"
	@echo ""

# Build all services
build:
	@echo "Building Docker images..."
	docker compose build

# Build with no cache
build-no-cache:
	@echo "Building Docker images (no cache)..."
	docker compose build --no-cache

# Start all services
up:
	@echo "Starting services..."
	docker compose up -d
	@echo ""
	@echo "Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

# Start with logs
up-logs:
	@echo "Starting services with logs..."
	docker compose up

# Stop all services
down:
	@echo "Stopping services..."
	docker compose down

# Restart all services
restart:
	@echo "Restarting services..."
	docker compose restart

# View logs from all services
logs:
	docker compose logs -f

# View backend logs
logs-backend:
	docker compose logs -f backend

# View frontend logs
logs-frontend:
	docker compose logs -f frontend

# Show running containers
ps:
	docker compose ps

# Show container stats
stats:
	docker stats

# Open shell in backend container
shell-backend:
	docker compose exec backend bash

# Open shell in frontend container
shell-frontend:
	docker compose exec frontend sh

# Run backend tests
test-backend:
	docker compose exec backend pytest

# Check backend health
health-backend:
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "Backend not responding"

# Check frontend health
health-frontend:
	@curl -s http://localhost:3000/health || echo "Frontend not responding"

# Backup databases
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	docker compose exec backend tar czf /app/backup.tar.gz /app/data
	docker cp knowledge-base-backend:/app/backup.tar.gz ./backups/backup-$$(date +%Y%m%d-%H%M%S).tar.gz
	docker compose exec backend rm /app/backup.tar.gz
	@echo "Backup created in ./backups/"

# Clean up (remove containers, volumes)
clean:
	@echo "Cleaning up..."
	docker compose down -v
	@echo "Cleanup complete"

# Rebuild everything from scratch
rebuild: clean build-no-cache up
	@echo "Rebuild complete"

# Update dependencies
update:
	@echo "Updating dependencies..."
	docker compose pull
	docker compose up -d

# Prune Docker system
prune:
	@echo "Pruning Docker system..."
	docker system prune -af --volumes
	@echo "Prune complete"

# Show disk usage
disk-usage:
	docker system df

# Validate docker-compose.yml
validate:
	docker compose config

# Install development dependencies
dev-setup:
	@echo "Setting up development environment..."
	cd backend && python -m venv venv && . venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@echo "Development setup complete"
