# Deployment Scripts

Automated installation and deployment scripts for MentalHealth Platform.

## 🚀 Quick Install (Recommended)

### One-Command Local Installation

Install everything on your machine with Docker:

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-all.sh | bash
```

### One-Command Kubernetes Installation

Install on Kubernetes cluster:

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-k8s-all.sh | bash
```

---

## 📜 Available Scripts

### Complete Installation Scripts (From Scratch)

| Script | Description | Usage |
|--------|-------------|-------|
| `install-all.sh` | Complete automated local installation. Installs Docker, clones repo, deploys everything | `./scripts/install-all.sh` |
| `install-k8s-all.sh` | Complete Kubernetes installation. Installs kubectl, sets up cluster, deploys platform | `./scripts/install-k8s-all.sh` |

### Deployment Scripts (Existing Setup)

| Script | Description | Usage |
|--------|-------------|-------|
| `deploy-local.sh` | Deploy platform locally with Docker Compose | `./scripts/deploy-local.sh` |
| `deploy-k8s.sh` | Deploy platform to Kubernetes cluster | `./scripts/deploy-k8s.sh` |
| `setup.sh` | Initial setup: migrations and admin user creation | `./scripts/setup.sh` |
| `setup-monitoring.sh` | Deploy monitoring stack (Prometheus, Grafana) | `./scripts/setup-monitoring.sh` |

---

## 🔍 Script Details

### install-all.sh

**Complete automated installation from scratch**

**What it does:**
1. Detects operating system (Ubuntu, Debian, CentOS, macOS)
2. Installs all dependencies (Docker, Docker Compose, Git, etc.)
3. Clones the MentalHealth repository
4. Generates secure configuration with random secrets
5. Builds and starts all services
6. Runs database migrations
7. Creates admin user
8. Shows access URLs

**Supported OS:**
- Ubuntu 20.04+, Debian 11+
- CentOS 8+, Rocky Linux, AlmaLinux
- Fedora 38+
- macOS 12+

**Time:** 5-10 minutes

**Usage:**
```bash
# Run directly from GitHub
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-all.sh | bash

# Or download and run
wget https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-all.sh
chmod +x install-all.sh
./install-all.sh
```

**What you get:**
- Complete platform running on http://localhost:3000
- Admin panel at http://localhost:3000/admin
- API docs at http://localhost:8080/docs
- All services configured and ready

---

### install-k8s-all.sh

**Complete Kubernetes installation from scratch**

**What it does:**
1. Installs kubectl
2. Installs Docker (for minikube/kind)
3. Offers cluster options:
   - Use existing cluster
   - Create new minikube cluster
   - Create new kind cluster
4. Clones repository
5. Generates Kubernetes secrets
6. Deploys all components (PostgreSQL HA, Redis, Backend, Frontend)
7. Creates admin user
8. Shows access instructions

**Time:** 10-15 minutes

**Usage:**
```bash
# Run directly from GitHub
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-k8s-all.sh | bash

# Or download and run
wget https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-k8s-all.sh
chmod +x install-k8s-all.sh
./install-k8s-all.sh
```

**What you get:**
- Production-ready Kubernetes deployment
- High availability PostgreSQL (3 replicas)
- Redis cluster (3 replicas)
- Auto-scaling Backend and Frontend
- NGINX Ingress Controller
- All configured with port-forward instructions

---

### deploy-local.sh

**Deploy platform locally (assumes Docker is installed)**

**Prerequisites:**
- Docker installed and running
- Docker Compose installed
- Git repository cloned

**Usage:**
```bash
cd MentalHealth
./scripts/deploy-local.sh
```

**Time:** 3-5 minutes

---

### deploy-k8s.sh

**Deploy platform to Kubernetes (assumes kubectl is configured)**

**Prerequisites:**
- kubectl installed and configured
- Kubernetes cluster accessible
- Git repository cloned

**Environment Variables:**
- `DOCKER_REGISTRY`: Docker registry URL (default: ghcr.io/therealHZL)
- `IMAGE_TAG`: Image tag (default: latest)
- `NAMESPACE`: Kubernetes namespace (default: mentalhealth)

**Usage:**
```bash
cd MentalHealth
./scripts/deploy-k8s.sh

# With custom registry and tag
DOCKER_REGISTRY=myregistry.com IMAGE_TAG=v1.0.0 ./scripts/deploy-k8s.sh
```

**Time:** 5-8 minutes

---

### setup.sh

**Initial setup and admin user creation**

**What it does:**
- Detects environment (Docker/Kubernetes/Host)
- Runs database migrations
- Creates admin user with custom credentials

**Usage:**
```bash
cd MentalHealth
./scripts/setup.sh

# Follow prompts for admin credentials
```

**Time:** 1-2 minutes

---

### setup-monitoring.sh

**Deploy complete monitoring stack**

**What it does:**
- Deploys Prometheus (2 replicas)
- Deploys Grafana (2 replicas) with dashboards
- Deploys Alertmanager (2 replicas)
- Creates ServiceMonitors for auto-discovery
- Configures metrics collection

**Prerequisites:**
- Kubernetes cluster
- Platform already deployed

**Usage:**
```bash
cd MentalHealth
./scripts/setup-monitoring.sh
```

**Access:**
```bash
# Grafana
kubectl port-forward -n monitoring svc/grafana-service 3001:3000
# http://localhost:3001 (admin/admin)

# Prometheus
kubectl port-forward -n monitoring svc/prometheus-service 9090:9090
# http://localhost:9090
```

**Time:** 3-5 minutes

---

## 🎯 Usage Examples

### Scenario 1: Quick Local Testing

```bash
# One command to install everything
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-all.sh | bash

# Access at http://localhost:3000
# Login with admin credentials shown at the end
```

### Scenario 2: Production Kubernetes Deployment

```bash
# Install on Kubernetes
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-k8s-all.sh | bash

# Choose option 1 to use existing cluster
# Follow prompts for admin credentials

# Access via port-forward or LoadBalancer IP
```

### Scenario 3: Development Workflow

```bash
# Clone repo first
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth

# Deploy locally
./scripts/deploy-local.sh

# Make changes to code

# Redeploy
./scripts/deploy-local.sh

# View logs
docker-compose -f docker-compose.full.yaml logs -f backend
```

### Scenario 4: Staging + Production Environments

```bash
# Deploy to staging
NAMESPACE=mentalhealth-staging ./scripts/deploy-k8s.sh

# Test staging
kubectl port-forward -n mentalhealth-staging svc/frontend-service 3000:3000

# Deploy to production
NAMESPACE=mentalhealth-prod IMAGE_TAG=v1.0.0 ./scripts/deploy-k8s.sh
```

---

## 🛠️ Script Features

All scripts include:

- ✅ **Colored output** (blue=info, green=success, yellow=warning, red=error)
- ✅ **Error handling** (exit on error with `set -e`)
- ✅ **Progress indicators** (step-by-step progress)
- ✅ **Health checks** (wait for services to be ready)
- ✅ **OS detection** (Ubuntu, Debian, CentOS, macOS)
- ✅ **Secure secrets** (auto-generated with OpenSSL)
- ✅ **Idempotent** (safe to run multiple times)
- ✅ **Detailed logging** (clear error messages)
- ✅ **ASCII art** (beautiful terminal output)

---

## 📖 Documentation

For more information:

- [Quick Install Guide](../docs/QUICK_INSTALL.md) - One-command installation
- [Deployment Scripts Guide](../docs/DEPLOYMENT_SCRIPTS.md) - Detailed documentation
- [Deployment Guide](../docs/DEPLOYMENT_GUIDE.md) - Manual deployment steps
- [Complete System Overview](../docs/COMPLETE_SYSTEM_OVERVIEW.md) - Architecture details

---

## 🐛 Troubleshooting

### Script won't run

```bash
# Make sure script is executable
chmod +x scripts/*.sh

# Run with bash explicitly
bash scripts/install-all.sh
```

### Docker permission denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### Port already in use

```bash
# Find what's using the port
sudo lsof -i :3000
sudo lsof -i :8080

# Kill the process
kill -9 <PID>
```

### Services won't start

```bash
# Check logs
docker-compose -f docker-compose.full.yaml logs

# Or for Kubernetes
kubectl logs -n mentalhealth -l app=backend
```

---

## 🔒 Security Notes

**Generated Secrets:**
- All scripts generate cryptographically secure random secrets
- Database passwords: 32 characters
- JWT keys: 64 character hex
- Never commit `.env` or `app-secrets-generated.yaml` files

**Default Admin:**
- Email: admin@mentalhealth.com
- Username: admin
- Password: admin123
- ⚠️ **Change immediately after first login!**

---

## 📊 Comparison

| Feature | install-all.sh | deploy-local.sh | install-k8s-all.sh | deploy-k8s.sh |
|---------|----------------|-----------------|-------------------|---------------|
| Installs Docker | ✅ | ❌ | ✅ | ❌ |
| Installs kubectl | ❌ | ❌ | ✅ | ❌ |
| Clones repo | ✅ | ❌ | ✅ | ❌ |
| Generates secrets | ✅ | ✅ | ✅ | ✅ |
| Creates admin | ✅ | ❌ | ✅ | ❌ |
| One-command | ✅ | ✅ | ✅ | ✅ |
| Environment | Local | Local | Kubernetes | Kubernetes |
| Prerequisites | None | Docker | None | kubectl |

---

## 📝 Script Maintenance

To update scripts:

1. Test in development environment
2. Update version number in script header
3. Update documentation
4. Test on clean VM
5. Commit and push changes

---

**Maintained By**: MentalHealth Platform Team
**Last Updated**: 2025-10-30
**Script Versions**: v1.0.0
