# DevOps Pipeline — Stage-by-Stage Guide

This document explains every stage of the CI/CD pipeline built for the Real-Time Web Traffic Analyzer, explaining **what it does**, **why it exists**, and **how to demonstrate it**.

---

## Pipeline Overview

```
Code Push
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│                    GitHub Actions CI                      │
│  1. Lint (ruff + eslint)                                  │
│  2. Unit + Integration Tests + Coverage                   │
│  3. Security Audit (pip-audit + npm audit)                │
│  4. Docker Build + Trivy Image Scan                       │
└──────────────────────────────────────────────────────────┘
   │ On main branch merge only ▼
┌──────────────────────────────────────────────────────────┐
│                   GitHub Actions CD                       │
│  5. Build & Push Versioned Images → GHCR                 │
│  6. Deploy → Staging + Health Check                       │
│  7. Manual Approval Gate                                  │
│  8. Deploy → Production + Auto Rollback                   │
└──────────────────────────────────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│                 Live Production Stack                      │
│  9. Prometheus Metrics Scraping (5s intervals)            │
│ 10. Grafana Dashboards (pre-provisioned)                  │
│ 11. Alert Rules → Slack/Discord Webhook                   │
└──────────────────────────────────────────────────────────┘
```

---

## Stage 1: Version Control Strategy

**Branch Model:**
```
main         ← Protected. Only receives PR merges. Triggers CD.
  └─ develop ← Integration branch for feature work.
       └─ feature/xyz ← Developer feature branches.
```

**Why Conventional Commits?**
Commit messages like `feat: add anomaly detection` or `fix: handle naive datetimes` make the Git history machine-readable. This enables automatic changelogs, semantic versioning, and clear PR attribution.

**Branch Protection Rules (configure on GitHub):**
- Require 1 PR review before merging to `main`
- Require CI status checks to pass (lint + test + docker-build)
- No force pushes allowed on `main` or `develop`

---

## Stage 2: Linting (ruff + eslint)

**File:** `.github/workflows/ci.yml` → `lint` job

**Python (ruff):**
- Replaces flake8 + isort + pyupgrade. Extremely fast (Rust-based).
- Runs `ruff check` (lint rules: E, F, W, I, N, UP, B, SIM)
- Runs `ruff format --check` (Black-compatible formatter)

**JavaScript (eslint):**
- Configured in `frontend/.eslintrc.cjs`
- Enforces react/recommended + react-hooks rules
- Runs `npm run lint`

**Why?** Catching style, complexity, and type-safety issues in CI prevents them from ever reaching code review — much cheaper to fix early than after a PR discussion.

---

## Stage 3: Unit & Integration Tests

**File:** `.github/workflows/ci.yml` → `test` job

- Runs `pytest tests/ --cov=backend.app --cov-report=xml`
- Coverage threshold enforced at **70%** in `pyproject.toml`
- Test categories:
  - **Unit**: parser, anomaly detection math, percentile calculations
  - **Integration**: FastAPI endpoints (health, collect, stats, events, logs)
- Coverage report uploaded as a GitHub Actions artifact

**Why?** Tests guarantee behavioral correctness. The 70% floor prevents coverage regression — tests must be written, not deleted, to keep CI green.

---

## Stage 4: Dependency Security Auditing

**File:** `.github/workflows/ci.yml` → `security-audit` job

- `pip-audit -r backend/requirements.txt` — scans Python packages against CVE advisories
- `npm audit --audit-level=high` — checks Node packages for high/critical CVEs

**Why?** Supply chain attacks via compromised packages are a top attack vector. Automated audits in CI mean no vulnerable dependency ever reaches a deployed image.

---

## Stage 5: Multi-Stage Docker Build + Trivy Scan

**File:** `.github/workflows/ci.yml` → `docker-build-scan` job

**Multi-Stage Builds:**
- `backend/Dockerfile`: `python:3.13-slim` builder → minimal `python:3.13-slim` runtime
- `frontend/Dockerfile`: `node:20-alpine` build → `nginx:1.25-alpine` static serving
- Non-root user (`appuser:1000`) in all containers
- Health checks defined in each `Dockerfile`

**Trivy Vulnerability Scanner:**
- Scans the built `traffic-backend:ci-test` image for OS-level and library CVEs
- Flags `CRITICAL` and `HIGH` severity issues

**Why?** Container images have their own attack surface (base OS CVEs). Trivy catches issues that `pip-audit` misses because it also scans the OS layer.

---

## Stage 6: Registry — GitHub Container Registry (GHCR)

**File:** `.github/workflows/cd.yml` → `publish` job

- Triggers only on push to `main` branch
- Logs in using `${{ secrets.GITHUB_TOKEN }}` (no extra secret needed)
- Builds and pushes 3 images with two tags:
  - `:latest` — always points to newest successful build
  - `:<sha8>` — immutable version tag (e.g. `:a3f7b912`)
- Example images pushed:
  - `ghcr.io/YOUR_USER/traffic-analyzer/backend:latest`
  - `ghcr.io/YOUR_USER/traffic-analyzer/frontend:latest`
  - `ghcr.io/YOUR_USER/traffic-analyzer/demo-site:latest`

**Why GHCR?** It's free for public/private repos, natively integrated with GitHub Actions tokens, and versioned images support exact rollbacks.

---

## Stage 7: Deploy to Staging (Auto Health-Check)

**File:** `.github/workflows/cd.yml` → `deploy-staging` job

- SSH into staging VM using `${{ secrets.STAGING_SSH_KEY }}`
- `docker compose pull` — downloads the freshly-built images
- `docker compose up -d --remove-orphans` — rolling restart
- Polls `/health` endpoint up to 12× (5s intervals = 60s timeout)
- If all polls fail: automatic rollback by `docker compose restart`

**Why?** Staging is a production-clone environment. Deploying here first catches integration issues (DB migrations, environment differences) before they hit real users.

---

## Stage 8: Manual Approval Gate → Production

**File:** `.github/workflows/cd.yml` → `deploy-production` job

```yaml
environment:
  name: production
```

This GitHub `environment` configuration adds a **required reviewer** approval step. The CD workflow pauses at this job and a human must approve before production deployment starts.

**Why?** Fully automated deployments to production are dangerous for user-facing services. The gate ensures a human verifies staging is healthy before proceeding.

---

## Stage 9: Production Deploy with Automatic Rollback

**File:** `.github/workflows/cd.yml` → `deploy-production` job (continued)

- SSH into production VM
- Pull new images and bring stack up
- Health check polls `/health` (backend) and `/healthz` (demo site) up to 15× (4s intervals = 60s)
- If health checks pass: deployment is marked successful
- If health checks fail: `docker compose down && docker compose up -d` (restores previous state)

**Why Rollback?** Zero-downtime deployments require a safety net. Automatic rollback means a bad deployment is corrected in seconds without requiring manual intervention in the middle of the night.

---

## Stage 10: Infrastructure as Code (Terraform)

**Location:** `infra/terraform/`

Provisions an AWS EC2 instance (t3.micro, Free Tier eligible) with:
- VPC, Internet Gateway, public subnet, route tables
- Security Group: App ports (80, 443, 3000, 8000, 8080, 9090, 3001) open; **PostgreSQL port 5432 strictly internal-only**
- Ubuntu 22.04 LTS with Docker Engine provisioned via `user_data`

**Why Terraform?** The infrastructure is version-controlled, repeatable, and reviewable. Anyone can recreate the entire server from `terraform apply` in minutes.

---

## Stage 11: Prometheus Metrics + Grafana Dashboards

**Location:** `monitoring/`

- Prometheus scrapes `/metrics` every 5 seconds
- Pre-provisioned Grafana dashboard loads automatically from `monitoring/grafana/provisioning/dashboards/traffic-dashboard.json`
- Panels: Active Users gauge, Request Throughput time series, P95 Latency, Error Rate %, Anomaly count

**Why?** Application-level observability is separate from deployment logs. Prometheus + Grafana is industry-standard for production monitoring and debugging.

---

## Stage 12: Alerting

**Location:** `monitoring/prometheus/alert.rules.yml`

| Alert | Expression | Severity |
|---|---|---|
| `ServiceDown` | `up{job="traffic-backend"} == 0` for 30s | Critical |
| `HighErrorRate` | Error rate > 15% for 30s | Critical |
| `HighLatency` | P95 > 500ms for 30s | Warning |
| `AnomalyDetected` | `increase(anomalies_total[1m]) > 0` | Warning |

Alerts dispatch to the webhook URL configured in `ALERT_WEBHOOK_URL` (Slack/Discord compatible).

---

## How to Present This Pipeline

1. **Show the GitHub repo** — point to `/.github/workflows/` and explain CI vs CD
2. **Make a commit** — push any change to the feature branch, show CI running in GitHub Actions
3. **Merge to main** — show CD trigger: images built → GHCR → staging → approval gate → production
4. **Open Grafana** — show live metrics updating from real simulator traffic
5. **Run `make demo-traffic`** — show anomaly alerts appear on dashboard and (if webhook configured) in Slack/Discord
6. **Run `make smoke`** — show post-deploy smoke test passing

*This pipeline is a complete, production-ready DevOps workflow demonstrating every stage of modern continuous delivery.*
