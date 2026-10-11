# Deployment Guide — Step-by-Step Commands

This guide covers everything you need to go from a fresh clone to a fully deployed, monitored production stack.

---

## Part 1: GitHub Repository Setup

### Step 1.1 — Create GitHub Repo

```bash
# On GitHub.com: Create new repository named "traffic-analyzer"
# Set it to Public (required for free GHCR image pulls) or Private

# Then on your local machine:
cd traffic-analyzer/

# If the remote hasn't been set yet:
git remote add origin https://github.com/YOUR_USERNAME/traffic-analyzer.git
```

### Step 1.2 — First Push (Feature Branch)

```bash
# Add all project files
git add -A

# Commit with conventional commit message
git commit -m "feat: complete real-time traffic analyzer with devops pipeline"

# Push the feature branch (CI will run on this push)
git push -u origin feature/traffic-devops-pipeline
```

### Step 1.3 — Create and Merge Pull Request

1. Open GitHub → Your repo → "Compare & pull request"
2. Set base branch to `main` (you may need to create `main` first)
3. Review the PR template checklist
4. Merge the PR → This triggers the **CD workflow** to build and push images to GHCR

### Step 1.4 — Protect Main Branch (Recommended)

On GitHub.com: Settings → Branches → Add branch protection rule for `main`:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass (select: `lint`, `test`, `docker-build-scan`)
- ✅ Do not allow bypassing the above settings

---

## Part 2: Adding GitHub Secrets

Go to GitHub.com → Your repo → Settings → Secrets and variables → Actions → New repository secret.

### Required Secrets

| Secret Name | Value |
|---|---|
| `SSH_HOST` | Public IP of your production VM |
| `SSH_USER` | `ubuntu` (or your VM user) |
| `SSH_PRIVATE_KEY` | Contents of your `.pem` private key file |
| `STAGING_SSH_HOST` | Public IP of staging VM (can be same as prod for testing) |
| `STAGING_SSH_USER` | `ubuntu` |
| `STAGING_SSH_KEY` | Same or separate private key for staging |

### Optional Secrets

| Secret Name | Value |
|---|---|
| `ALERT_WEBHOOK_URL` | Slack/Discord incoming webhook URL |

**Adding the SSH key:**
```bash
# On your local machine, copy key content to clipboard
cat ~/.ssh/your-key.pem | clip        # Windows
cat ~/.ssh/your-key.pem | pbcopy      # macOS

# Paste as the value for SSH_PRIVATE_KEY secret on GitHub
```

### Production Environment Setup

Go to: Settings → Environments → New environment → Name: `production`
- Add a Required reviewer (yourself or a team member)
- This creates the manual approval gate for production deployments

---

## Part 3: Provision the Server (Terraform)

### Step 3.1 — Prerequisites

```bash
# Install Terraform (download from terraform.io or use chocolatey on Windows)
choco install terraform

# Configure AWS credentials (never commit these)
aws configure
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region: us-east-1
```

### Step 3.2 — Create SSH Key Pair

```bash
# On AWS Console: EC2 → Key Pairs → Create key pair
# Name: "traffic-analyzer-key"
# Type: RSA, Format: .pem
# Download and store securely:
mkdir -p ~/.ssh
mv ~/Downloads/traffic-analyzer-key.pem ~/.ssh/
chmod 400 ~/.ssh/traffic-analyzer-key.pem
```

### Step 3.3 — Review and Apply Infrastructure

```bash
cd infra/terraform/

# Initialize Terraform providers
terraform init

# Preview what will be created (NO resources created yet)
terraform plan

# Review the plan carefully, then apply:
# NOTE: This creates billable cloud resources. t3.micro is AWS Free Tier eligible.
terraform apply

# After apply completes, note the outputs:
# server_public_ip = "x.x.x.x"
# dashboard_url = "http://x.x.x.x:3000"
```

### Step 3.4 — Update GitHub Secrets with Server IP

Take the `server_public_ip` from Terraform output and update:
- `SSH_HOST` secret on GitHub

---

## Part 4: First Deploy to Production

### Step 4.1 — SSH into the Server

```bash
ssh -i ~/.ssh/traffic-analyzer-key.pem ubuntu@YOUR_SERVER_IP
```

### Step 4.2 — Clone Repository on Server

```bash
# On the server:
sudo mkdir -p /opt/traffic-analyzer
sudo chown ubuntu:ubuntu /opt/traffic-analyzer

git clone https://github.com/YOUR_USERNAME/traffic-analyzer.git /opt/traffic-analyzer
cd /opt/traffic-analyzer

# Create production env file
cp .env.example .env
nano .env  # Edit DATABASE_URL, ALERT_WEBHOOK_URL, etc.
```

### Step 4.3 — Pull Images and Start Stack

```bash
# On the server:
cd /opt/traffic-analyzer

# If using GHCR private registry, authenticate first:
echo "$GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Pull and start all containers
docker compose pull
docker compose up -d

# Check health
curl http://localhost:8000/health
curl http://localhost:8080/healthz
```

### Step 4.4 — Trigger CD via GitHub

After the initial setup, all future deploys happen automatically via GitHub Actions:

```bash
# On your local machine, make any change and push to main:
git commit -m "fix: example deploy trigger"
git push origin main
# → CD workflow starts automatically
# → Staging deployment → Manual approval prompt → Production deployment
```

---

## Part 5: Accessing Deployed Services

After deployment, services are available at:

```
Dashboard:   http://YOUR_SERVER_IP:3000
Demo Site:   http://YOUR_SERVER_IP:8080
API Health:  http://YOUR_SERVER_IP:8000/health
API Docs:    http://YOUR_SERVER_IP:8000/docs
Prometheus:  http://YOUR_SERVER_IP:9090
Grafana:     http://YOUR_SERVER_IP:3001  (login: admin / admin)
```

---

## Part 6: Manual Rollback Procedure

If you need to rollback a failed deployment manually:

### Option A — Docker Compose Rollback

```bash
ssh -i ~/.ssh/traffic-analyzer-key.pem ubuntu@YOUR_SERVER_IP

cd /opt/traffic-analyzer

# Pin to a specific image tag (from GHCR)
export PREVIOUS_TAG="abc123ef"  # Replace with previous commit SHA

# Update docker-compose.yml to use the pinned tag, then:
docker compose up -d --force-recreate

# Or simply restart current state:
docker compose restart
```

### Option B — Git Revert + CD Re-deploy

```bash
# On your local machine:
git revert HEAD              # Creates a revert commit
git push origin main         # Triggers CD pipeline with the reverted code
# → New images built from reverted code → auto-deployed
```

---

## Part 7: Stopping the Stack

### Local Development

```bash
make down
# Or:
docker compose down
```

### Production Server (safely stop and clean up)

```bash
ssh -i ~/.ssh/traffic-analyzer-key.pem ubuntu@YOUR_SERVER_IP
cd /opt/traffic-analyzer
docker compose down
```

### Destroy Cloud Infrastructure (CAUTION — permanently destroys server)

```bash
# ONLY run this if you want to permanently delete the EC2 instance and all AWS resources:
cd infra/terraform/
terraform destroy
# This will NOT delete data in S3 or RDS if you added those separately
```

---

## Troubleshooting

### Backend not healthy after deploy

```bash
# Check backend logs
docker compose logs backend --tail=50

# Check database connection
docker compose exec backend python -c "from backend.app.database import init_db; init_db()"
```

### Frontend can't connect to WebSocket

Ensure `VITE_API_URL` in frontend build points to the correct backend URL, or that the nginx proxy is routing correctly.

### Demo site not generating logs for tailing

Verify the shared volume `demo-logs` is correctly mounted in both `demo-site` and `backend` containers:
```bash
docker compose exec backend ls /var/log/nginx/
```
