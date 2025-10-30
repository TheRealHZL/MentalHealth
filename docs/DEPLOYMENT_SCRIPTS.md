# Deployment Scripts Documentation

This document describes the automated deployment scripts for the MentalHealth Platform. These scripts automate the entire deployment process, from local development to production Kubernetes clusters.

## 📁 Available Scripts

| Script | Purpose | Environment |
|--------|---------|-------------|
| `deploy-local.sh` | Deploy locally using Docker Compose | Local Development |
| `deploy-k8s.sh` | Deploy to Kubernetes cluster | Production/Staging |
| `setup.sh` | Initial setup and admin user creation | All Environments |
| `setup-monitoring.sh` | Setup monitoring stack (Prometheus, Grafana) | Kubernetes |

---

## 🚀 Quick Start

### Local Development Deployment

Deploy the entire platform locally in **3 minutes**:

```bash
# One-command deployment
./scripts/deploy-local.sh

# Create admin user
./scripts/setup.sh
```

That's it! Access the application at:
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Kubernetes Production Deployment

Deploy to Kubernetes cluster in **5 minutes**:

```bash
# Deploy entire platform
./scripts/deploy-k8s.sh

# Setup monitoring (optional)
./scripts/setup-monitoring.sh

# Create admin user
./scripts/setup.sh
```

---

## 📖 Script Details

### 1. Local Deployment (`deploy-local.sh`)

**Purpose**: Automated local deployment using Docker Compose

**What it does**:
1. ✅ Checks Docker and Docker Compose installation
2. ✅ Creates `.env` file with secure defaults if not exists
3. ✅ Stops existing containers and volumes
4. ✅ Builds Docker images with no cache
5. ✅ Starts all services (PostgreSQL, Redis, Backend, Frontend)
6. ✅ Waits for database to be ready
7. ✅ Runs database migrations automatically
8. ✅ Performs health checks on all services
9. ✅ Shows service URLs and useful commands

**Usage**:
```bash
# Basic usage
./scripts/deploy-local.sh

# View logs after deployment
docker-compose -f docker-compose.full.yaml logs -f

# Stop services
docker-compose -f docker-compose.full.yaml down

# Stop and remove volumes
docker-compose -f docker-compose.full.yaml down -v
```

**Requirements**:
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB disk space

**Environment Variables**:

The script creates a default `.env` file with:
- Secure random secrets (SECRET_KEY, JWT_SECRET_KEY)
- Default database credentials
- Development-friendly defaults

**Output Example**:
```
======================================
MentalHealth Platform - Local Deployment
======================================

[INFO] Checking Docker installation...
[SUCCESS] Docker is installed
[INFO] Building Docker images...
[SUCCESS] Docker images built successfully
[INFO] Starting services...
[SUCCESS] Services started
[INFO] Waiting for database to be ready...
[SUCCESS] Database is ready
[SUCCESS] Backend is ready
[SUCCESS] Frontend is ready

======================================
Deployment Complete!
======================================

Access the application at:
  Frontend:  http://localhost:3000
  Backend:   http://localhost:8000
  API Docs:  http://localhost:8000/docs
```

---

### 2. Kubernetes Deployment (`deploy-k8s.sh`)

**Purpose**: Automated production deployment to Kubernetes

**What it does**:
1. ✅ Checks kubectl installation and cluster connection
2. ✅ Creates namespace with labels
3. ✅ Generates secure secrets automatically
4. ✅ Creates ConfigMaps for all services
5. ✅ Creates Storage Classes and Network Policies
6. ✅ Deploys PostgreSQL StatefulSet (HA with 3 replicas)
7. ✅ Deploys Redis Deployment (3 replicas)
8. ✅ Deploys Backend with Horizontal Pod Autoscaling
9. ✅ Deploys Frontend with Horizontal Pod Autoscaling
10. ✅ Deploys NGINX Ingress Controller
11. ✅ Optionally deploys Monitoring Stack
12. ✅ Waits for all pods to be ready
13. ✅ Shows service URLs and access instructions

**Usage**:
```bash
# Basic usage
./scripts/deploy-k8s.sh

# Set custom image tag
IMAGE_TAG=v1.2.3 ./scripts/deploy-k8s.sh

# Use custom Docker registry
DOCKER_REGISTRY=myregistry.com/myproject ./scripts/deploy-k8s.sh

# Both together
DOCKER_REGISTRY=myregistry.com/myproject IMAGE_TAG=v1.2.3 ./scripts/deploy-k8s.sh
```

**Requirements**:
- kubectl configured with cluster access
- Kubernetes cluster 1.24+
- Storage provisioner for PersistentVolumeClaims
- LoadBalancer service support (or use port-forwarding)

**Environment Variables**:
- `DOCKER_REGISTRY`: Docker registry URL (default: `ghcr.io/therealHZL`)
- `IMAGE_TAG`: Docker image tag (default: `latest`)
- `NAMESPACE`: Kubernetes namespace (default: `mentalhealth`)

**Generated Resources**:

| Resource Type | Count | Description |
|--------------|-------|-------------|
| Namespace | 1 | mentalhealth namespace |
| Secret | 1 | Auto-generated secure credentials |
| ConfigMap | 3 | PostgreSQL, Redis, App configs |
| StatefulSet | 1 | PostgreSQL HA cluster (3 replicas) |
| Deployment | 4 | Redis, Backend, Frontend, Ingress |
| Service | 5 | All services with appropriate types |
| HPA | 2 | Backend and Frontend autoscaling |
| NetworkPolicy | 3 | Security policies |
| Ingress | 1 | NGINX Ingress with SSL |

**Secrets Generated**:

The script automatically generates secure secrets:
- Database password (32 characters)
- Redis password (32 characters)
- JWT secret key (64 characters hex)
- App secret key (64 characters hex)

These are saved to `k8s/secrets/app-secrets-generated.yaml`.

**Output Example**:
```
======================================
MentalHealth Platform - K8s Deployment
======================================

[INFO] Connected to Kubernetes cluster
[INFO] Using cluster: production-cluster
[SUCCESS] Namespace created
[SUCCESS] Secrets applied
[SUCCESS] PostgreSQL deployment started
[SUCCESS] PostgreSQL is ready
[SUCCESS] Redis is ready
[SUCCESS] Backend is ready
[SUCCESS] Frontend is ready
[SUCCESS] Ingress Controller deployed

======================================
Deployment Complete!
======================================

Access the application at:
  Application: http://10.20.30.40
  API:         http://10.20.30.40/api

Port forwarding commands:
  Frontend:  kubectl port-forward -n mentalhealth svc/frontend-service 3000:3000
  Backend:   kubectl port-forward -n mentalhealth svc/backend-service 8000:8000
```

---

### 3. Initial Setup (`setup.sh`)

**Purpose**: Initial configuration and admin user creation

**What it does**:
1. ✅ Detects deployment environment (Docker/K8s/Host)
2. ✅ Creates `.env` file if not exists
3. ✅ Installs Python dependencies (if on host)
4. ✅ Runs database migrations
5. ✅ Creates admin user with custom credentials
6. ✅ Shows access instructions

**Usage**:
```bash
# Interactive setup
./scripts/setup.sh

# You will be prompted for:
# - Admin email (default: admin@mentalhealth.com)
# - Admin username (default: admin)
# - Admin password (default: admin123)
```

**Environment Detection**:

The script automatically detects where it's running:
- **Docker**: Uses `docker-compose exec` commands
- **Kubernetes**: Uses `kubectl exec` commands
- **Host**: Runs commands directly

**Requirements**:
- Python 3.11+ (if running on host)
- Database must be running and accessible
- Alembic migrations must be available

**Admin User Creation**:

The script creates an admin user with:
- Custom email address
- Custom username
- Custom password (or default)
- `role: admin`
- `is_active: true`
- `is_verified: true`

**Output Example**:
```
======================================
MentalHealth Platform - Setup
======================================

[INFO] Running on host system
[SUCCESS] .env file exists
[SUCCESS] Python is installed
[SUCCESS] Database migrations completed
[INFO] Creating admin user...

Enter admin email [admin@mentalhealth.com]: admin@example.com
Enter admin username [admin]: superadmin
Enter admin password [admin123]: ********

[SUCCESS] Admin user setup completed

======================================
Setup Complete!
======================================

Admin credentials:
  Email:    admin@example.com
  Username: superadmin
  Password: ********

Important: Please change the admin password after first login!

Next steps:
  1. Login with admin credentials
  2. Go to Admin Panel: http://localhost:3000/admin
  3. Upload training datasets
  4. Train AI models
  5. Activate trained models
```

---

### 4. Monitoring Setup (`setup-monitoring.sh`)

**Purpose**: Deploy complete monitoring stack (Prometheus, Grafana, Alertmanager)

**What it does**:
1. ✅ Creates monitoring namespace
2. ✅ Deploys Prometheus with RBAC
3. ✅ Deploys Grafana with pre-configured dashboards
4. ✅ Deploys Alertmanager with alerts
5. ✅ Creates ServiceMonitors for automatic discovery
6. ✅ Configures metrics collection for:
   - Backend application
   - PostgreSQL database
   - Redis cache
   - Kubernetes cluster
7. ✅ Shows access URLs and credentials

**Usage**:
```bash
# Deploy monitoring stack
./scripts/setup-monitoring.sh

# Access Grafana
kubectl port-forward -n monitoring svc/grafana-service 3001:3000

# Access Prometheus
kubectl port-forward -n monitoring svc/prometheus-service 9090:9090
```

**Requirements**:
- Kubernetes cluster with kubectl access
- Application must be deployed first
- 4GB RAM minimum for monitoring stack
- 100GB storage for Prometheus data

**Deployed Components**:

| Component | Replicas | Purpose | Port |
|-----------|----------|---------|------|
| Prometheus | 2 | Metrics collection and storage | 9090 |
| Grafana | 2 | Metrics visualization | 3000 |
| Alertmanager | 2 | Alert management | 9093 |

**Pre-configured Dashboards**:
1. **Application Metrics**
   - Request rate, latency, error rate
   - API endpoint performance
   - User activity metrics

2. **PostgreSQL Metrics**
   - Connections, queries per second
   - Cache hit ratio
   - Replication lag

3. **Redis Metrics**
   - Memory usage
   - Hit/miss ratio
   - Connected clients

4. **Kubernetes Cluster**
   - Node resources
   - Pod status
   - Network traffic

5. **AI Training Metrics**
   - Training job status
   - Model performance
   - Dataset usage

**Grafana Default Credentials**:
- Username: `admin`
- Password: `admin`
- ⚠️ **Change password after first login!**

**Prometheus Targets**:

The script automatically configures Prometheus to scrape:
- Backend: `http://backend-service:8000/metrics`
- PostgreSQL: `http://postgresql-service:9187/metrics`
- Redis: `http://redis-service:9121/metrics`

**Output Example**:
```
======================================
MentalHealth - Monitoring Setup
======================================

[SUCCESS] Monitoring namespace created
[SUCCESS] Prometheus deployed
[SUCCESS] Prometheus is ready
[SUCCESS] Grafana deployed
[SUCCESS] Grafana is ready
[SUCCESS] Alertmanager deployed

======================================
Monitoring Setup Complete!
======================================

Access monitoring dashboards:

  Prometheus:   kubectl port-forward -n monitoring svc/prometheus-service 9090:9090
                http://localhost:9090

  Grafana:      kubectl port-forward -n monitoring svc/grafana-service 3001:3000
                http://localhost:3001

  Alertmanager: kubectl port-forward -n monitoring svc/alertmanager-service 9093:9093
                http://localhost:9093

Grafana default credentials:
  Username: admin
  Password: admin
  Please change the password after first login!

Available Grafana Dashboards:
  - Application Metrics
  - PostgreSQL Metrics
  - Redis Metrics
  - Kubernetes Cluster Metrics
  - AI Training Metrics
```

---

## 🔧 Advanced Usage

### Custom Environment Variables

**Local Deployment**:
```bash
# Edit .env file before deployment
cp .env.example .env
nano .env

# Then deploy
./scripts/deploy-local.sh
```

**Kubernetes Deployment**:
```bash
# Edit secrets before deployment
nano k8s/secrets/app-secrets-generated.yaml

# Then deploy
./scripts/deploy-k8s.sh
```

### Multiple Environments

Deploy to different environments:

```bash
# Development
ENVIRONMENT=dev NAMESPACE=mentalhealth-dev ./scripts/deploy-k8s.sh

# Staging
ENVIRONMENT=staging NAMESPACE=mentalhealth-staging ./scripts/deploy-k8s.sh

# Production
ENVIRONMENT=production NAMESPACE=mentalhealth-prod ./scripts/deploy-k8s.sh
```

### Selective Deployment

Deploy only specific components:

```bash
# Only database
kubectl apply -f k8s/database/

# Only backend
kubectl apply -f k8s/app/backend-deployment.yaml

# Only monitoring
./scripts/setup-monitoring.sh
```

### Scaling

Scale deployments after deployment:

```bash
# Scale backend
kubectl scale deployment backend-deployment -n mentalhealth --replicas=5

# Scale frontend
kubectl scale deployment frontend-deployment -n mentalhealth --replicas=5

# Scale Redis
kubectl scale deployment redis-deployment -n mentalhealth --replicas=5
```

---

## 🐛 Troubleshooting

### Local Deployment Issues

**Problem**: Docker daemon not running
```bash
# Check Docker status
docker info

# Start Docker daemon (Linux)
sudo systemctl start docker

# Start Docker Desktop (Mac/Windows)
# Use the Docker Desktop application
```

**Problem**: Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.full.yaml
```

**Problem**: Database not ready
```bash
# Check database logs
docker-compose -f docker-compose.full.yaml logs postgres

# Restart database
docker-compose -f docker-compose.full.yaml restart postgres
```

### Kubernetes Deployment Issues

**Problem**: Pods not starting
```bash
# Check pod status
kubectl get pods -n mentalhealth

# Describe pod for events
kubectl describe pod <pod-name> -n mentalhealth

# Check logs
kubectl logs <pod-name> -n mentalhealth
```

**Problem**: Image pull errors
```bash
# Check if image exists
docker pull ghcr.io/therealHZL/mentalhealth-backend:latest

# Update image pull secrets
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n mentalhealth
```

**Problem**: Services not accessible
```bash
# Check service endpoints
kubectl get endpoints -n mentalhealth

# Check if pods are ready
kubectl get pods -n mentalhealth

# Test service internally
kubectl run -it --rm debug --image=alpine --restart=Never -n mentalhealth -- sh
wget -O- http://backend-service:8000/health
```

**Problem**: Storage issues
```bash
# Check PVC status
kubectl get pvc -n mentalhealth

# Check storage class
kubectl get storageclass

# Describe PVC for events
kubectl describe pvc <pvc-name> -n mentalhealth
```

### Monitoring Issues

**Problem**: Prometheus not collecting metrics
```bash
# Check Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-service 9090:9090
# Visit http://localhost:9090/targets

# Check ServiceMonitors
kubectl get servicemonitor -n mentalhealth

# Check if metrics endpoint is accessible
kubectl exec -n mentalhealth <backend-pod> -- wget -O- http://localhost:8000/metrics
```

**Problem**: Grafana dashboards empty
```bash
# Check Grafana data sources
kubectl logs -n monitoring -l app=grafana

# Verify Prometheus connection in Grafana
# Settings → Data Sources → Prometheus → Test

# Reimport dashboards
kubectl delete configmap grafana-dashboards -n monitoring
kubectl apply -f k8s/monitoring/grafana/grafana-dashboards.yaml
kubectl rollout restart deployment/grafana-deployment -n monitoring
```

---

## 📊 Monitoring and Observability

After deployment, monitor your application:

### Application Health

**Local (Docker)**:
```bash
# Backend health
curl http://localhost:8000/health

# View all logs
docker-compose -f docker-compose.full.yaml logs -f

# View specific service logs
docker-compose -f docker-compose.full.yaml logs -f backend
```

**Kubernetes**:
```bash
# Check all pods
kubectl get pods -n mentalhealth -w

# View pod logs
kubectl logs -f -n mentalhealth -l app=backend

# Check pod health
kubectl exec -n mentalhealth <pod-name> -- wget -O- http://localhost:8000/health
```

### Database Health

**PostgreSQL**:
```bash
# Docker
docker-compose -f docker-compose.full.yaml exec postgres pg_isready

# Kubernetes
kubectl exec -n mentalhealth postgresql-0 -- pg_isready
```

**Redis**:
```bash
# Docker
docker-compose -f docker-compose.full.yaml exec redis redis-cli ping

# Kubernetes
kubectl exec -n mentalhealth <redis-pod> -- redis-cli ping
```

### Metrics Endpoints

- Backend Metrics: `http://localhost:8000/metrics`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`

---

## 🔐 Security Considerations

### Secrets Management

**Local Development**:
- Use `.env` file (never commit to git)
- Rotate secrets regularly
- Use strong passwords

**Kubernetes Production**:
- Use Kubernetes Secrets (base64 encoded)
- Consider using external secret management:
  - HashiCorp Vault
  - AWS Secrets Manager
  - Azure Key Vault
  - Google Secret Manager

### Network Security

The deployment scripts configure:
- Network Policies (default deny)
- RBAC for all services
- TLS for Ingress (configure in ingress.yaml)
- ModSecurity with OWASP CRS

### Additional Security Steps

1. **Change default credentials**:
   - Admin user password
   - Grafana admin password
   - Database passwords

2. **Enable TLS**:
   ```bash
   # Add TLS cert to ingress
   kubectl create secret tls tls-secret \
     --cert=path/to/cert.pem \
     --key=path/to/key.pem \
     -n mentalhealth
   ```

3. **Configure firewalls**:
   - Allow only necessary ports
   - Restrict access by IP

4. **Enable audit logging**:
   - Application logs
   - Kubernetes audit logs
   - Database audit logs

---

## 📈 Production Checklist

Before going to production, ensure:

- [ ] All secrets are changed from defaults
- [ ] TLS certificates are configured
- [ ] Database backups are configured
- [ ] Monitoring and alerting are set up
- [ ] Resource limits are appropriate
- [ ] HPA is configured correctly
- [ ] Network policies are tested
- [ ] Disaster recovery plan is in place
- [ ] CI/CD pipeline is configured
- [ ] Load testing is performed
- [ ] Security scanning is complete
- [ ] Documentation is up to date

---

## 🆘 Support

For issues with deployment scripts:

1. Check the troubleshooting section above
2. Review logs for error messages
3. Check GitHub Issues: https://github.com/TheRealHZL/MentalHealth/issues
4. Consult the main documentation:
   - [QUICK_START.md](../QUICK_START.md)
   - [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
   - [COMPLETE_SYSTEM_OVERVIEW.md](../COMPLETE_SYSTEM_OVERVIEW.md)

---

## 📝 Script Maintenance

### Updating Scripts

When updating deployment scripts:

1. Test in development environment first
2. Update documentation
3. Update version comments in scripts
4. Test rollback procedures
5. Update CI/CD pipelines if needed

### Script Versions

Current versions:
- `deploy-local.sh`: v1.0.0
- `deploy-k8s.sh`: v1.0.0
- `setup.sh`: v1.0.0
- `setup-monitoring.sh`: v1.0.0

---

**Last Updated**: 2025-10-30
**Maintained By**: MentalHealth Platform Team
