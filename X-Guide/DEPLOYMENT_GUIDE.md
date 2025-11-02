# MentalHealth Platform - Complete Deployment Guide

## 🎯 Overview

This guide covers everything you need to deploy the MentalHealth platform in different environments:
- Local Development with Docker Compose
- Production on Kubernetes
- CI/CD with GitHub Actions

## 📋 Table of Contents

1. [Quick Start (Local Development)](#quick-start-local-development)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [CI/CD Setup](#cicd-setup)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start (Local Development)

### Prerequisites

- Docker Desktop 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB free disk space

### Step 1: Clone Repository

```bash
git clone https://github.com/YourOrg/MentalHealth.git
cd MentalHealth
```

### Step 2: Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (optional - AI runs locally with custom models)
# No external API keys required for AI functionality!
```

### Step 3: Start Services

```bash
# Start all services (Backend, Frontend, PostgreSQL, Redis)
docker-compose -f docker-compose.full.yaml up -d

# View logs
docker-compose -f docker-compose.full.yaml logs -f

# Check status
docker-compose -f docker-compose.full.yaml ps
```

### Step 4: Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (profile: tools)

### Step 5: Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.full.yaml exec backend alembic upgrade head

# (Optional) Seed test data
docker-compose -f docker-compose.full.yaml exec backend python scripts/seed_data.py
```

### Stop Services

```bash
docker-compose -f docker-compose.full.yaml down

# Remove all data (clean start)
docker-compose -f docker-compose.full.yaml down -v
```

---

## 🐳 Docker Deployment

### Building Images

#### Backend

```bash
# Development
docker build -t mentalhealth/backend:dev -f Dockerfile .

# Production
docker build -t mentalhealth/backend:latest -f Dockerfile.production .
```

#### Frontend

```bash
cd frontend
docker build -t mentalhealth/frontend:latest .
```

### Running with Docker Compose

#### Basic Setup (Backend + Databases)

```bash
docker-compose up -d
```

#### Full Stack (Backend + Frontend + Monitoring)

```bash
docker-compose -f docker-compose.full.yaml up -d
```

#### With Monitoring Stack

```bash
docker-compose -f docker-compose.full.yaml --profile monitoring up -d
```

This starts:
- Prometheus (http://localhost:9090)
- Grafana (http://localhost:3001) - admin/admin

#### With Development Tools

```bash
docker-compose -f docker-compose.full.yaml --profile tools up -d
```

This adds:
- pgAdmin (http://localhost:5050)

### Docker Health Checks

```bash
# Check all container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Check specific service logs
docker-compose -f docker-compose.full.yaml logs backend
docker-compose -f docker-compose.full.yaml logs frontend
```

---

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- 3+ nodes with 4 CPU, 8GB RAM each
- 260GB storage available
- Helm 3+ (optional)

### Quick Deploy

```bash
cd k8s
./deploy.sh
```

The script will:
1. Check prerequisites
2. Verify secrets are updated
3. Deploy base infrastructure
4. Deploy databases (PostgreSQL, Redis)
5. Deploy ingress controller
6. Deploy monitoring stack
7. Deploy applications

### Manual Deployment

#### Step 1: Update Secrets

**CRITICAL**: Update all secrets before deploying!

```bash
# Generate secure passwords
openssl rand -base64 32

# Update these files:
# - k8s/secrets/postgres-secret.yaml
# - k8s/secrets/redis-secret.yaml
# - k8s/secrets/app-secrets.yaml
```

#### Step 2: Deploy Infrastructure

```bash
# Create namespace
kubectl apply -f k8s/base/namespace.yaml

# Deploy ConfigMaps
kubectl apply -f k8s/configmaps/

# Deploy Secrets (after updating!)
kubectl apply -f k8s/secrets/

# Deploy Storage
kubectl apply -f k8s/base/storageclass.yaml
```

#### Step 3: Deploy Databases

```bash
# PostgreSQL (StatefulSet with HA)
kubectl apply -f k8s/database/

# Wait for PostgreSQL
kubectl wait --for=condition=ready pod -l app=postgresql -n mentalhealth --timeout=300s

# Redis
kubectl apply -f k8s/cache/

# Wait for Redis
kubectl wait --for=condition=ready pod -l app=redis -n mentalhealth --timeout=180s
```

#### Step 4: Deploy Applications

```bash
# Backend
kubectl apply -f k8s/app/backend-deployment.yaml

# Frontend
kubectl apply -f k8s/app/frontend-deployment.yaml

# Wait for applications
kubectl wait --for=condition=ready pod -l app=backend -n mentalhealth --timeout=300s
kubectl wait --for=condition=ready pod -l app=frontend -n mentalhealth --timeout=300s
```

#### Step 5: Deploy Ingress

```bash
# Ingress Controller
kubectl apply -f k8s/ingress/nginx-ingress-controller.yaml

# Update domains in ingress-rules.yaml, then:
kubectl apply -f k8s/ingress/ingress-rules.yaml
```

#### Step 6: Deploy Monitoring

```bash
# Prometheus
kubectl apply -f k8s/monitoring/prometheus/

# Grafana
kubectl apply -f k8s/monitoring/grafana/

# Alertmanager
kubectl apply -f k8s/monitoring/alertmanager/
```

### Using Kustomize

```bash
cd k8s
kubectl apply -k .
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods -n mentalhealth

# Check services
kubectl get svc -n mentalhealth

# Check ingress
kubectl get ingress -n mentalhealth

# Get LoadBalancer IP
kubectl get svc ingress-nginx -n ingress-nginx
```

### Access Applications

#### Via Port Forwarding (Testing)

```bash
# Backend API
kubectl port-forward svc/backend-service 8000:8000 -n mentalhealth

# Frontend
kubectl port-forward svc/frontend-service 3000:3000 -n mentalhealth

# Grafana
kubectl port-forward svc/grafana 3000:3000 -n mentalhealth

# Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n mentalhealth
```

#### Via Ingress (Production)

Update DNS records to point to LoadBalancer IP:
- api.mentalhealth.example.com → Backend
- mentalhealth.example.com → Frontend
- grafana.mentalhealth.example.com → Grafana
- prometheus.mentalhealth.example.com → Prometheus

---

## 🔄 CI/CD Setup

### GitHub Actions Configuration

The project includes two workflows:

1. **ci-cd.yaml** - Main pipeline for build, test, and deploy
2. **security-scan.yaml** - Automated security scanning

### Required Secrets

Add these secrets in GitHub Settings → Secrets and variables → Actions:

```bash
# Container Registry (if using private registry)
DOCKER_USERNAME
DOCKER_PASSWORD

# Kubernetes (for auto-deployment)
KUBE_CONFIG  # base64-encoded kubeconfig

# Optional: Notifications
SLACK_WEBHOOK_URL
```

### Generate kubeconfig Secret

```bash
# Encode your kubeconfig
cat ~/.kube/config | base64 | pbcopy

# Add to GitHub Secrets as KUBE_CONFIG
```

### Pipeline Triggers

- **Push to main** → Build, test, scan, deploy to production
- **Push to develop** → Build, test, scan, deploy to staging
- **Pull Request** → Run tests only
- **Daily 2 AM UTC** → Security scans

### Manual Workflow Trigger

```bash
# Via GitHub UI:
Actions → CI/CD Pipeline → Run workflow

# Or via GitHub CLI:
gh workflow run ci-cd.yaml
```

### Monitoring Pipeline

View pipeline status:
- GitHub Actions tab
- Badge in README (add if desired)
- Slack notifications (if configured)

---

## 🔐 Environment Variables

### Backend (.env)

```bash
# Database
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=mentalhealth_db
DATABASE_USER=mentalhealth
DATABASE_PASSWORD=<strong-password>

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<strong-password>

# Security
JWT_SECRET=<min-32-chars-random-string>
ENCRYPTION_KEY=<32-bytes-base64>
SESSION_SECRET=<random-string>

# AI Configuration (uses custom PyTorch models - no external APIs needed)
# Optional external AI services (not required):
# OPENAI_API_KEY=sk-<your-key>
# ANTHROPIC_API_KEY=<your-key>

# Environment
ENVIRONMENT=production
LOG_LEVEL=info

# CORS
CORS_ORIGINS=https://mentalhealth.example.com

# API
API_PREFIX=/api/v1

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Frontend (.env.local)

```bash
# API
NEXT_PUBLIC_API_URL=https://api.mentalhealth.example.com
NEXT_PUBLIC_APP_URL=https://mentalhealth.example.com

# Environment
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
```

### Generating Secure Values

```bash
# JWT Secret (32+ chars)
openssl rand -hex 32

# Encryption Key (32 bytes)
openssl rand -base64 32

# Session Secret
openssl rand -base64 48

# Password
openssl rand -base64 24
```

---

## 🔧 Troubleshooting

### Docker Issues

#### Containers won't start

```bash
# Check logs
docker-compose -f docker-compose.full.yaml logs backend
docker-compose -f docker-compose.full.yaml logs frontend

# Check health
docker-compose -f docker-compose.full.yaml ps

# Restart services
docker-compose -f docker-compose.full.yaml restart
```

#### Database connection errors

```bash
# Check PostgreSQL is healthy
docker-compose -f docker-compose.full.yaml exec postgres pg_isready

# Connect to database
docker-compose -f docker-compose.full.yaml exec postgres psql -U mentalhealth -d mentalhealth_db

# Check migrations
docker-compose -f docker-compose.full.yaml exec backend alembic current
```

#### Port conflicts

```bash
# Check what's using ports
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :5432  # PostgreSQL

# Change ports in docker-compose.full.yaml
```

### Kubernetes Issues

#### Pods not starting

```bash
# Check pod status
kubectl get pods -n mentalhealth

# Describe pod for events
kubectl describe pod <pod-name> -n mentalhealth

# Check logs
kubectl logs <pod-name> -n mentalhealth

# Previous container logs (if crashlooping)
kubectl logs <pod-name> -n mentalhealth --previous
```

#### Image pull errors

```bash
# Check image exists
docker pull mentalhealth/backend:latest

# Check imagePullSecrets
kubectl get secrets -n mentalhealth

# Create pull secret if needed
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=$USERNAME \
  --docker-password=$TOKEN \
  --namespace=mentalhealth
```

#### Persistent volume issues

```bash
# Check PVCs
kubectl get pvc -n mentalhealth

# Check PVs
kubectl get pv

# Describe PVC
kubectl describe pvc <pvc-name> -n mentalhealth
```

#### Ingress not accessible

```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress rules
kubectl describe ingress mentalhealth-ingress -n mentalhealth

# Get LoadBalancer IP
kubectl get svc ingress-nginx -n ingress-nginx

# Check DNS
nslookup mentalhealth.example.com
```

### Database Issues

#### Migrations failing

```bash
# Docker
docker-compose -f docker-compose.full.yaml exec backend alembic current
docker-compose -f docker-compose.full.yaml exec backend alembic upgrade head

# Kubernetes
kubectl exec deployment/backend -n mentalhealth -- alembic current
kubectl exec deployment/backend -n mentalhealth -- alembic upgrade head
```

#### Connection pool exhausted

Check `max_connections` in PostgreSQL config and increase:

```bash
# Docker
docker-compose -f docker-compose.full.yaml exec postgres psql -U mentalhealth -c "SHOW max_connections;"

# Kubernetes
kubectl exec postgresql-0 -n mentalhealth -- psql -U postgres -c "SHOW max_connections;"
```

### Performance Issues

#### High memory usage

```bash
# Docker - check resource usage
docker stats

# Kubernetes - check resource usage
kubectl top pods -n mentalhealth
kubectl top nodes
```

#### Slow API responses

1. Check database query performance
2. Check Redis connection
3. Review application logs
4. Check monitoring dashboards (Grafana)
5. Enable query logging

---

## 📊 Monitoring

### Accessing Dashboards

**Docker Compose:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

**Kubernetes:**
```bash
kubectl port-forward svc/grafana 3000:3000 -n mentalhealth
kubectl port-forward svc/prometheus 9090:9090 -n mentalhealth
```

### Key Metrics to Monitor

- **API Response Time** - Should be < 200ms for 95th percentile
- **Database Connections** - Should be < 80% of max
- **Redis Memory** - Should be < 80% of limit
- **CPU Usage** - Should be < 70% average
- **Memory Usage** - Should be < 80% of limit
- **Error Rate** - Should be < 1%

### Alerts

Configure alerts in Prometheus/Alertmanager for:
- Service downtime
- High error rates
- Resource exhaustion
- Database connection issues
- Security events

---

## 🔒 Security Checklist

Before production deployment:

- [ ] All secrets updated with strong, random values
- [ ] TLS certificates configured (Let's Encrypt or manual)
- [ ] Network policies enabled
- [ ] RBAC properly configured
- [ ] Container images scanned for vulnerabilities
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Security headers enabled
- [ ] Log aggregation configured
- [ ] Disaster recovery plan documented

---

## 📚 Additional Resources

- [Kubernetes README](k8s/README.md)
- [Architecture Documentation](ENTERPRISE_ARCHITECTURE.md)
- [Security Audit](SECURITY_AUDIT_PHASE3.md)
- [Implementation Plan](IMPLEMENTATION_PLAN.md)
- [Phase Completion Logs](PHASE4-KUBERNETES-SETUP.md)

---

## 🆘 Support

For issues or questions:
1. Check logs first
2. Review this troubleshooting guide
3. Check GitHub Issues
4. Contact DevOps team

---

**Last Updated**: 2025-10-30
**Version**: 1.0.0
