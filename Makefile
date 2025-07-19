# PulseDev+ Makefile

.PHONY: help build deploy clean test lint

# Default target
help:
	@echo "PulseDev+ Commands:"
	@echo "  make build          - Build all Docker images"
	@echo "  make deploy         - Deploy to Kubernetes"
	@echo "  make dev            - Start development environment"
	@echo "  make clean          - Clean up resources"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run linting"
	@echo "  make logs           - View application logs"

# Development
dev:
	docker-compose up -d
	@echo "Development environment started at:"
	@echo "  Frontend: http://localhost:3000"
	@echo "  API: http://localhost:8000"
	@echo "  Grafana: http://localhost:3001"
	@echo "  n8n: http://localhost:5678"

dev-down:
	docker-compose down

# Build Docker images
build:
	@echo "Building CCM API..."
	docker build -t pulsedev-ccm-api:latest ./apps/ccm-api/
	@echo "Building Frontend..."
	docker build -f Dockerfile.frontend -t pulsedev-frontend:latest .
	@echo "All images built successfully!"

# Kubernetes deployment
deploy: build
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/postgres.yaml
	kubectl apply -f k8s/redis.yaml
	kubectl apply -f k8s/ccm-api.yaml
	kubectl apply -f k8s/frontend.yaml
	kubectl apply -f k8s/monitoring.yaml
	@echo "Deployment complete!"

# Delete Kubernetes resources
clean:
	kubectl delete namespace pulsedev-ccm --ignore-not-found=true
	docker-compose down -v
	@echo "Cleanup complete!"

# Testing
test:
	@echo "Running API tests..."
	cd apps/ccm-api && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	npm test
	@echo "Running plugin tests..."
	cd apps/vscode-plugin && npm test
	@echo "All tests completed!"

# Linting
lint:
	@echo "Linting Python code..."
	cd apps/ccm-api && python -m flake8 . --exclude=venv
	@echo "Linting TypeScript code..."
	npm run lint
	cd apps/vscode-plugin && npm run lint
	cd apps/browser-extension && npm run lint
	@echo "Linting complete!"

# Logs
logs:
	kubectl logs -f deployment/ccm-api -n pulsedev-ccm

logs-postgres:
	kubectl logs -f deployment/postgres -n pulsedev-ccm

logs-frontend:
	kubectl logs -f deployment/frontend -n pulsedev-ccm

# Plugin development
plugin-vscode:
	cd apps/vscode-plugin && npm run compile && npm run watch

plugin-browser:
	cd apps/browser-extension && npm run build && npm run watch

plugin-nvim:
	@echo "Neovim plugin ready for development in apps/nvim-plugin/"

# Database management
db-migrate:
	kubectl exec -it deployment/postgres -n pulsedev-ccm -- psql -U postgres -d pulsedev_ccm -f /docker-entrypoint-initdb.d/schema.sql

db-shell:
	kubectl exec -it deployment/postgres -n pulsedev-ccm -- psql -U postgres -d pulsedev_ccm

# Monitoring
metrics:
	@echo "Prometheus: http://localhost:9090"
	@echo "Grafana: http://localhost:3001 (admin/admin)"
	kubectl port-forward service/prometheus-service 9090:9090 -n pulsedev-ccm &
	kubectl port-forward service/grafana-service 3001:3000 -n pulsedev-ccm &

# Security scanning
security:
	@echo "Running security scans..."
	docker run --rm -v $(PWD):/src securecodewarrior/docker-scout:latest /src
	npm audit
	@echo "Security scan complete!"

# Performance testing
perf:
	@echo "Running performance tests..."
	cd apps/ccm-api && python -m pytest tests/performance/ -v
	@echo "Performance tests complete!"