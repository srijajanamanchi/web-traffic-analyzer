# Live Demo Script

A step-by-step walkthrough for demonstrating the Real-Time Web Traffic Analyzer and its full DevOps pipeline.

**Estimated demo duration: ~15–20 minutes**

---

## Pre-Demo Checklist

Before your presentation, ensure:
- [ ] `docker compose up -d` has been run and all containers are healthy
- [ ] `docker compose ps` shows all 8 services as "healthy"
- [ ] Dashboard is open at http://localhost:3000
- [ ] Demo Site is open at http://localhost:8080
- [ ] Grafana is open at http://localhost:3001 (admin/admin)
- [ ] GitHub repo is open in the browser (for CI/CD demo)

---

## Scene 1: The Demo Website (Real Traffic Source)

> **Talking point:** "This demo site represents any real website. The tracker snippet embedded on every page sends telemetry events to our collector API, exactly like analytics tools like Plausible or PostHog do."

1. Open **http://localhost:8080** in the browser
2. Point out the navigation: Home, Products, Contact, Slow Page, Broken Link
3. Click through a few pages:
   - Click **Products** → browse the product cards
   - Click **Contact** → fill in the form and submit it
   - Click **Slow Page** → observe the slow load time
4. Click **Broken Link (404)** → the custom 404 page appears

> "Every click, page load, and form submission is captured by `tracker.js` — a tiny 80-line resilient snippet that never blocks rendering and fails silently if the API is down."

---

## Scene 2: The Live Dashboard

> **Talking point:** "This is the real-time telemetry dashboard. It connects to our backend via WebSocket and updates live — every event from the demo site appears here within milliseconds."

1. Switch to the dashboard at **http://localhost:3000**
2. Point out the **Live Stream Active** indicator in the top-right (green pulse)
3. Show the **KPI cards** at the top:
   - Total Requests
   - Active Visitors Now
   - Unique Visitors
   - Error Rate (should show the 404 we just triggered)
   - P95 Latency (should show elevated latency from the `/slow` page)
4. Show the **Traffic Throughput chart** — highlight the time-series line
5. Show the **Status Code Donut** — point out the 4xx slice from our 404 hit
6. Show the **Top Endpoints table** — `/slow.html`, `/old-page`, `/index.html` should appear
7. Show the **Referrers table** and **Device/Browser Breakdown**

> "The system automatically identifies browser, OS, and device type from the User-Agent header using a rule-based parser — no third-party library needed."

---

## Scene 3: Generate a Traffic Spike (Anomaly Detection)

> **Talking point:** "The anomaly engine uses a rolling z-score algorithm. When traffic significantly deviates from the recent baseline, the system flags it automatically and can dispatch webhook alerts to Slack or Discord."

1. Open a terminal
2. Run the traffic spike:
   ```bash
   make spike
   # OR: make demo-traffic (runs all anomaly scenarios in sequence)
   ```
3. Switch back to the dashboard — watch the request throughput chart spike dramatically
4. Point out the **Anomaly Detection Panel** at the bottom — a `traffic_spike` alert should appear
5. Run the error surge:
   ```bash
   make errors
   ```
6. Watch the **Error Rate KPI** jump and an `error_surge` alert appear
7. Run the suspicious IP scanner:
   ```bash
   make scanner
   ```
8. A `suspicious_ip` alert appears with the attacker IP flagged

> "Each alert includes the z-score, the metric value vs baseline, and severity classification. In production, these fire to a configured Slack/Discord webhook."

---

## Scene 4: Grafana Observability

> **Talking point:** "Prometheus scrapes our `/metrics` endpoint every 5 seconds. Grafana dashboards are pre-provisioned automatically — no manual setup needed."

1. Switch to **http://localhost:3001** (admin/admin)
2. Navigate to Dashboards → Observability → "Web Traffic & System Observability"
3. Point out:
   - **Active Visitors Now** — Prometheus gauge
   - **Error Rate %** — turns red above 15%
   - **P95 Latency** — spikes from simulator
   - **Request Throughput** — real-time time-series
4. Show **http://localhost:9090** — Prometheus alerting rules:
   - Navigate to Status → Rules to show all defined alert conditions

---

## Scene 5: The CI Pipeline

> **Talking point:** "Every code push automatically triggers our CI pipeline — no manual steps. Let's watch it live."

1. On your local machine, make a trivial change:
   ```bash
   # Add a comment to README
   echo "<!-- demo trigger -->" >> README.md
   git add README.md
   git commit -m "docs: demo trigger for CI pipeline"
   git push origin feature/traffic-devops-pipeline
   ```
2. Open GitHub → Actions tab — show the CI workflow starting
3. Walk through the jobs:
   - **Lint** — ruff (Python) + eslint (frontend)
   - **Tests** — 27 tests, coverage report
   - **Security Audit** — pip-audit + npm audit
   - **Docker Build + Trivy Scan** — multi-stage build + CVE scan
4. All jobs should pass (green checkmarks)

---

## Scene 6: The CD Pipeline (Staging → Approval → Production)

> **Talking point:** "When a branch merges to `main`, CD kicks off automatically. Images are built, versioned, pushed to GHCR, deployed to staging, then paused for a human approval before going to production."

1. Create a PR on GitHub from your feature branch to `main`
2. Show the PR template (quality checklist)
3. Merge the PR — watch the CD workflow start
4. Walk through the CD jobs:
   - **Publish** — 3 images pushed to GHCR with SHA tags
   - **Deploy Staging** — SSH deploy + health check poll
   - **Approve** (manually click Approve in GitHub)
   - **Deploy Production** — SSH deploy + health check + automatic rollback ready

---

## Scene 7: Post-Deploy Smoke Test

> **Talking point:** "Our smoke test verifies the complete pipeline end-to-end after every deployment."

```bash
make smoke
```

Watch the output:
```
[1/4] Verifying API health endpoint...      ✓ /health OK: healthy
[2/4] Loading demo site home page...        ✓ Demo site home page loaded OK
[3/4] Sending telemetry pageview event...   ✓ Event collected successfully
[4/4] Verifying event in /api/events...     ✓ Event verified in API
✨ All smoke tests passed! Pipeline is healthy.
```

---

## Scene 8: Infrastructure as Code

> **Talking point:** "The entire cloud infrastructure is defined in Terraform — version-controlled, reviewable, and reproducible in minutes."

1. Show `infra/terraform/main.tf` — EC2 instance with Docker provisioning
2. Show `infra/terraform/security_groups.tf` — highlight that PostgreSQL port 5432 is **closed to the public internet**
3. Show `infra/terraform/outputs.tf` — all endpoint URLs are output automatically

```bash
cd infra/terraform/
terraform plan   # Preview (no resources created without apply)
```

---

## Closing Talking Points

- **Collection**: Dual-source (JS tracker + Nginx log tailer) for maximum coverage
- **Analysis**: Pure Python, no external analytics service — p50/p95/p99 latency, z-score anomaly detection
- **Visualization**: WebSocket real-time feed, Recharts, Tailwind dark theme
- **CI**: Lint + test + audit + Trivy scan on every push
- **CD**: GHCR registry + staging + manual gate + production + auto-rollback
- **IaC**: Terraform provisions server, network, and security groups
- **Observability**: Prometheus metrics + Grafana dashboards + 4 alert rules
- **Security**: No secrets in repo, non-root containers, DB port isolated, pre-commit hooks
