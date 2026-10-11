# =============================================================================
# Real-Time Web Traffic Analyzer — Developer Makefile
# =============================================================================
# Usage:
#   make up           Start the full local Docker Compose stack
#   make down         Stop and remove all containers
#   make test         Run Python unit + integration tests with coverage
#   make lint         Run ruff (Python) and eslint (frontend)
#   make simulate     Start continuous traffic simulation (demo mode)
#   make demo-traffic Run the end-to-end demo traffic sequence (spike + errors + scanner)
#   make smoke        Run post-deploy smoke tests against localhost
#   make load-test    Run Locust headless load test (50 users, 60s)
#   make build        Build Docker images locally
#   make logs         Tail logs from all containers
#   make ps           Show running container status

.PHONY: up down test lint simulate demo-traffic smoke load-test build logs ps restart clean help

# Configuration overrides
API_URL ?= http://localhost:8000
DEMO_URL ?= http://localhost:8080
COMPOSE = docker compose

# =============================================================================
# Stack Lifecycle
# =============================================================================

up:
	@echo "▶  Starting full Real-Time Traffic Analyzer stack..."
	$(COMPOSE) up -d
	@echo ""
	@echo "  ✓ Dashboard:    http://localhost:3000"
	@echo "  ✓ Demo Site:    http://localhost:8080"
	@echo "  ✓ API Health:   http://localhost:8000/health"
	@echo "  ✓ API Docs:     http://localhost:8000/docs"
	@echo "  ✓ Prometheus:   http://localhost:9090"
	@echo "  ✓ Grafana:      http://localhost:3001  (admin/admin)"
	@echo ""

down:
	@echo "■  Stopping all containers..."
	$(COMPOSE) down

restart:
	@echo "↻  Restarting all services..."
	$(COMPOSE) restart

build:
	@echo "⚙  Building all Docker images locally..."
	$(COMPOSE) build --no-cache

logs:
	$(COMPOSE) logs -f --tail=60

ps:
	$(COMPOSE) ps

clean:
	@echo "🧹 Removing stopped containers and stale volumes..."
	$(COMPOSE) down -v

# =============================================================================
# Testing
# =============================================================================

test:
	@echo "🧪 Running Python unit & integration tests with coverage..."
	python -m pytest tests/ --cov=backend.app --cov-report=term-missing -v -p no:warnings

smoke:
	@echo "🔬 Running post-deploy smoke test against live stack..."
	python tests/smoke_test.py --api-url $(API_URL) --demo-url $(DEMO_URL)

load-test:
	@echo "⚡ Starting Locust headless load test (50 users, 60s)..."
	locust -f tests/load_test.py \
		--host=$(API_URL) \
		--users 50 \
		--spawn-rate 10 \
		--run-time 60s \
		--headless \
		--html load-test-report.html

# =============================================================================
# Code Quality
# =============================================================================

lint:
	@echo "🔍 Running ruff linter on Python code..."
	python -m ruff check backend/ simulator/ tests/
	python -m ruff format --check backend/ simulator/ tests/
	@echo "🔍 Running ESLint on frontend code..."
	cd frontend && npm run lint

# =============================================================================
# Traffic Generation & Simulation
# =============================================================================

simulate:
	@echo "🌐 Starting continuous traffic simulator (Ctrl+C to stop)..."
	python simulator/simulator.py \
		--demo-url $(DEMO_URL) \
		--collector-url $(API_URL)/api/collect \
		--mode continuous \
		--rate 2.0 \
		--duration 0

demo-traffic:
	@echo "🎬 Running full end-to-end demo traffic sequence..."
	@echo "   Sequence: Baseline → Traffic Spike → Error Surge → Suspicious IP Scanner"
	python simulator/simulator.py \
		--demo-url $(DEMO_URL) \
		--collector-url $(API_URL)/api/collect \
		--mode demo

spike:
	@echo "⚡ Triggering rapid traffic spike..."
	python simulator/simulator.py \
		--demo-url $(DEMO_URL) \
		--collector-url $(API_URL)/api/collect \
		--mode spike

errors:
	@echo "❌ Triggering error surge (repeated 404s)..."
	python simulator/simulator.py \
		--demo-url $(DEMO_URL) \
		--collector-url $(API_URL)/api/collect \
		--mode errors

scanner:
	@echo "🛡️  Triggering suspicious IP scanner simulation..."
	python simulator/simulator.py \
		--demo-url $(DEMO_URL) \
		--collector-url $(API_URL)/api/collect \
		--mode scanner

# =============================================================================
# Help
# =============================================================================

help:
	@echo ""
	@echo "Real-Time Web Traffic Analyzer - Developer Make Commands"
	@echo ""
	@echo "  Stack:              make up | down | restart | build | logs | ps | clean"
	@echo "  Testing:            make test | smoke | load-test"
	@echo "  Code Quality:       make lint"
	@echo "  Traffic Gen:        make simulate | demo-traffic | spike | errors | scanner"
	@echo ""
	@echo "  Override variables: make smoke API_URL=http://your-server:8000"
	@echo ""
