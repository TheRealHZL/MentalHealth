# Phase 4 Week 3-4 Part 2: Kubernetes Cluster Setup

## Implementation Summary

Complete Kubernetes infrastructure for the MentalHealth platform with High Availability, monitoring, and security features.

## What Was Implemented

### 1. PostgreSQL StatefulSet (High Availability)
✅ **File**: `database/postgresql-statefulset.yaml`
- 3 replicas for HA
- Pod anti-affinity for distribution across nodes
- Persistent storage (50Gi per instance)
- Health checks (liveness & readiness probes)
- PostgreSQL Exporter sidecar for metrics
- Resource limits: 2Gi RAM, 2 CPU cores per pod
- Optimized configuration for production workloads

✅ **File**: `database/postgresql-service.yaml`
- ClusterIP service for application access
- Headless service for StatefulSet DNS
- Metrics service for Prometheus scraping

### 2. Redis Deployment
✅ **File**: `cache/redis-deployment.yaml`
- 3 replicas for high availability
- Pod anti-affinity for node distribution
- Redis Exporter sidecar for monitoring
- Password-protected access
- Persistent configuration via ConfigMap
- Resource limits: 1Gi RAM, 1 CPU core per pod

✅ **File**: `cache/redis-service.yaml`
- ClusterIP service for application access
- Metrics service for Prometheus scraping

### 3. Ingress Controller (NGINX)
✅ **File**: `ingress/nginx-ingress-controller.yaml`
- NGINX Ingress Controller deployment (3 replicas)
- RBAC configuration (ServiceAccount, ClusterRole, ClusterRoleBinding)
- Security features:
  - ModSecurity with OWASP CRS enabled
  - TLS 1.2/1.3 only
  - Strong cipher suites
- LoadBalancer service for external access
- Prometheus metrics endpoint

✅ **File**: `ingress/ingress-rules.yaml`
- Application ingress (API + Frontend)
- Monitoring ingress (Grafana + Prometheus)
- TLS/SSL configuration with cert-manager
- Security headers:
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - X-XSS-Protection
  - Referrer-Policy
  - Permissions-Policy
- Rate limiting (100 req/min, 10 RPS)
- Basic auth for monitoring dashboards

### 4. ConfigMaps & Secrets

#### ConfigMaps
✅ **File**: `configmaps/postgres-config.yaml`
- PostgreSQL configuration (postgresql.conf)
- Optimized for performance and HA
- WAL settings for replication
- Connection pooling settings
- Logging configuration

✅ **File**: `configmaps/redis-config.yaml`
- Redis configuration (redis.conf)
- Memory management (768MB max)
- Persistence settings (RDB + AOF)
- Security settings
- Performance optimization

✅ **File**: `configmaps/app-config.yaml`
- Application environment variables
- Database connection settings
- Redis connection settings
- API configuration
- Security settings
- Rate limiting configuration
- Feature flags

#### Secrets
✅ **File**: `secrets/postgres-secret.yaml`
- PostgreSQL username & password
- Exporter DSN for metrics
- Instructions for generating secure secrets

✅ **File**: `secrets/redis-secret.yaml`
- Redis password
- Instructions for secure generation

✅ **File**: `secrets/app-secrets.yaml`
- JWT secret
- OpenAI API key
- SMTP password
- Encryption key
- Session secret

✅ **File**: `secrets/monitoring-auth.yaml`
- Basic auth for monitoring dashboards
- htpasswd format

### 5. Monitoring Stack

#### Prometheus
✅ **File**: `monitoring/prometheus/prometheus-config.yaml`
- Comprehensive scrape configurations:
  - Kubernetes API servers
  - Kubernetes nodes
  - Kubernetes pods
  - PostgreSQL metrics
  - Redis metrics
  - NGINX Ingress metrics
- Alert rules:
  - High CPU/memory usage
  - Disk space warnings
  - PostgreSQL health checks
  - Redis health checks
- Recording rules for aggregation
- Alertmanager integration

✅ **File**: `monitoring/prometheus/prometheus-deployment.yaml`
- Prometheus deployment (2 replicas)
- RBAC configuration for Kubernetes discovery
- 30-day retention
- 100Gi persistent storage
- Resource limits: 2Gi RAM, 2 CPU cores

#### Grafana
✅ **File**: `monitoring/grafana/grafana-config.yaml`
- Prometheus datasource configuration
- Pre-configured dashboards:
  - Kubernetes Cluster Overview
  - PostgreSQL Monitoring
  - Redis Monitoring
- Dashboard provisioning

✅ **File**: `monitoring/grafana/grafana-deployment.yaml`
- Grafana deployment (2 replicas)
- Secure admin credentials
- Plugin installation
- 10Gi persistent storage
- Resource limits: 512Mi RAM, 500m CPU

#### Alertmanager
✅ **File**: `monitoring/alertmanager/alertmanager-config.yaml`
- Email notification configuration
- Routing rules by severity
- Alert grouping and deduplication
- Inhibition rules
- Template support

✅ **File**: `monitoring/alertmanager/alertmanager-deployment.yaml`
- Alertmanager deployment (2 replicas)
- Cluster mode for HA
- Resource limits: 256Mi RAM, 200m CPU

### 6. Additional Infrastructure

✅ **File**: `base/namespace.yaml`
- mentalhealth namespace with labels

✅ **File**: `base/storageclass.yaml`
- fast-ssd StorageClass
- Examples for AWS, GCP, Azure
- Volume expansion enabled
- Retain reclaim policy

✅ **File**: `base/network-policy.yaml`
- Default deny ingress policy
- Allow rules for:
  - PostgreSQL (only from app pods)
  - Redis (only from app pods)
  - Backend (from ingress + frontend)
  - Frontend (from ingress)
  - Monitoring (Prometheus, Grafana)
- DNS egress allowed for all pods

✅ **File**: `kustomization.yaml`
- Kustomize configuration for easy deployment
- Common labels and annotations
- Image version management
- Resource ordering

✅ **File**: `deploy.sh`
- Automated deployment script
- Prerequisite checks
- Secret validation
- Step-by-step deployment
- Status verification
- Color-coded output

✅ **File**: `README.md`
- Comprehensive documentation
- Deployment instructions
- Verification steps
- Monitoring guides
- Scaling procedures
- Backup & recovery
- Troubleshooting guide
- Security considerations
- Production checklist

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Internet / Users                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              NGINX Ingress Controller (3 replicas)           │
│  - TLS Termination                                          │
│  - Rate Limiting                                            │
│  - ModSecurity / OWASP CRS                                  │
└────────┬────────────────────────────┬───────────────────────┘
         │                            │
         ▼                            ▼
┌──────────────────┐        ┌─────────────────────┐
│  Frontend (3)    │        │  Backend API (3)    │
│  Next.js         │        │  FastAPI            │
└──────────────────┘        └─────┬───────┬───────┘
                                  │       │
                    ┌─────────────┘       └────────────┐
                    ▼                                   ▼
┌────────────────────────────────┐    ┌─────────────────────────┐
│  PostgreSQL StatefulSet (3)    │    │  Redis Deployment (3)   │
│  - Primary + 2 Replicas        │    │  - Shared Cache         │
│  - Automatic Failover          │    │  - Session Store        │
│  - 50Gi per instance           │    │  - 768Mi per instance   │
└────────────────────────────────┘    └─────────────────────────┘
                    │                                   │
                    └─────────────┬───────────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   Monitoring Stack                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Prometheus   │  │  Grafana     │  │ Alertmanager │     │
│  │ (2 replicas) │  │ (2 replicas) │  │ (2 replicas) │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Resource Requirements

### Minimum Cluster Size
- **Nodes**: 3 (for HA)
- **CPU per node**: 4 cores
- **RAM per node**: 8GB
- **Storage per node**: 100GB SSD

### Total Resource Allocation
- **PostgreSQL**: 6Gi RAM, 6 CPU cores (3 replicas × 2Gi/2CPU)
- **Redis**: 3Gi RAM, 3 CPU cores (3 replicas × 1Gi/1CPU)
- **Ingress**: 1.5Gi RAM, 1.5 CPU cores (3 replicas × 512Mi/500m)
- **Prometheus**: 4Gi RAM, 4 CPU cores (2 replicas × 2Gi/2CPU)
- **Grafana**: 1Gi RAM, 1 CPU cores (2 replicas × 512Mi/500m)
- **Alertmanager**: 512Mi RAM, 400m CPU (2 replicas × 256Mi/200m)

**Total**: ~16Gi RAM, ~16 CPU cores

### Storage Requirements
- **PostgreSQL**: 150Gi (3 × 50Gi)
- **Prometheus**: 100Gi
- **Grafana**: 10Gi

**Total**: 260Gi

## Security Features

1. **Network Policies**
   - Default deny all ingress
   - Explicit allow rules per service
   - Pod-to-pod isolation

2. **Secrets Management**
   - Kubernetes secrets for sensitive data
   - Instructions for secure generation
   - Ready for external secret managers

3. **Ingress Security**
   - TLS/SSL encryption
   - Security headers
   - Rate limiting
   - ModSecurity WAF
   - OWASP Core Rule Set

4. **RBAC**
   - Service accounts for Prometheus
   - Minimal permissions
   - ClusterRole for metrics collection

5. **Pod Security**
   - Non-root containers where possible
   - Read-only root filesystems
   - Security contexts defined

## Deployment Instructions

### Quick Start

```bash
cd k8s
./deploy.sh
```

### Manual Deployment

```bash
# 1. Update all secrets first!
# Edit files in secrets/ directory

# 2. Deploy using kustomize
kubectl apply -k .

# Or deploy step by step
kubectl apply -f base/
kubectl apply -f configmaps/
kubectl apply -f secrets/
kubectl apply -f database/
kubectl apply -f cache/
kubectl apply -f ingress/
kubectl apply -f monitoring/
```

### Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n mentalhealth

# Check services
kubectl get svc -n mentalhealth

# Check ingress
kubectl get ingress -n mentalhealth

# Check PVCs
kubectl get pvc -n mentalhealth
```

## Monitoring Access

### Port Forwarding (for testing)

```bash
# Grafana
kubectl port-forward svc/grafana 3000:3000 -n mentalhealth
# Access: http://localhost:3000

# Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n mentalhealth
# Access: http://localhost:9090

# Alertmanager
kubectl port-forward svc/alertmanager 9093:9093 -n mentalhealth
# Access: http://localhost:9093
```

### Production Access (via Ingress)

- **Grafana**: https://grafana.mentalhealth.example.com
- **Prometheus**: https://prometheus.mentalhealth.example.com
- **API**: https://api.mentalhealth.example.com
- **Frontend**: https://mentalhealth.example.com

## Next Steps

1. **Update Secrets**
   - Generate strong passwords
   - Update all secret files
   - Consider using external secret manager

2. **Configure DNS**
   - Point domains to LoadBalancer IP
   - Set up TLS certificates

3. **Deploy Applications**
   - Create backend deployment
   - Create frontend deployment
   - Link to databases

4. **Set Up Monitoring**
   - Configure Alertmanager notifications
   - Create custom Grafana dashboards
   - Set up log aggregation

5. **Production Hardening**
   - Enable Pod Security Standards
   - Set up backup automation
   - Configure disaster recovery
   - Implement GitOps (ArgoCD/Flux)

## Files Created

```
k8s/
├── README.md                                    # Comprehensive documentation
├── PHASE4-KUBERNETES-SETUP.md                   # This file
├── kustomization.yaml                           # Kustomize config
├── deploy.sh                                    # Automated deployment script
├── base/
│   ├── namespace.yaml                          # Namespace definition
│   ├── storageclass.yaml                       # Storage class config
│   └── network-policy.yaml                     # Network policies
├── database/
│   ├── postgresql-statefulset.yaml             # PostgreSQL HA cluster
│   └── postgresql-service.yaml                 # PostgreSQL services
├── cache/
│   ├── redis-deployment.yaml                   # Redis deployment
│   └── redis-service.yaml                      # Redis service
├── ingress/
│   ├── nginx-ingress-controller.yaml           # Ingress controller
│   └── ingress-rules.yaml                      # Ingress routing
├── configmaps/
│   ├── postgres-config.yaml                    # PostgreSQL config
│   ├── redis-config.yaml                       # Redis config
│   └── app-config.yaml                         # Application config
├── secrets/
│   ├── postgres-secret.yaml                    # PostgreSQL credentials
│   ├── redis-secret.yaml                       # Redis credentials
│   ├── app-secrets.yaml                        # App secrets
│   └── monitoring-auth.yaml                    # Monitoring auth
└── monitoring/
    ├── prometheus/
    │   ├── prometheus-config.yaml              # Prometheus config
    │   └── prometheus-deployment.yaml          # Prometheus deployment
    ├── grafana/
    │   ├── grafana-config.yaml                 # Grafana config
    │   └── grafana-deployment.yaml             # Grafana deployment
    └── alertmanager/
        ├── alertmanager-config.yaml            # Alertmanager config
        └── alertmanager-deployment.yaml        # Alertmanager deployment
```

**Total**: 25 Kubernetes configuration files

## Success Criteria ✅

- [x] PostgreSQL StatefulSet with HA (3 replicas)
- [x] Redis Deployment (3 replicas)
- [x] NGINX Ingress Controller with security features
- [x] ConfigMaps for all services
- [x] Secrets for sensitive data
- [x] Prometheus monitoring with comprehensive scraping
- [x] Grafana with pre-configured dashboards
- [x] Alertmanager with notification routing
- [x] Network policies for security
- [x] Storage classes configured
- [x] Automated deployment script
- [x] Comprehensive documentation

## Production Checklist

Before deploying to production:

- [ ] Update all secrets with strong, random passwords
- [ ] Configure proper domain names in ingress rules
- [ ] Set up TLS certificates (cert-manager or manual)
- [ ] Configure email/Slack for Alertmanager
- [ ] Set up database backups
- [ ] Configure resource limits based on load testing
- [ ] Enable Pod Security Standards
- [ ] Set up log aggregation
- [ ] Configure HPA (Horizontal Pod Autoscaler)
- [ ] Document disaster recovery procedures
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring alerts
- [ ] Test failover scenarios

## Phase 4 Completion Status

**Week 3-4 Part 2: Kubernetes Cluster Setup** ✅ **COMPLETED**

All required components implemented with production-grade configuration, monitoring, and security features.
