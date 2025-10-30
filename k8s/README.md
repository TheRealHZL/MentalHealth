# Kubernetes Cluster Setup - MentalHealth Platform

This directory contains all Kubernetes configurations for deploying the MentalHealth platform in a production environment.

## Overview

The infrastructure includes:
- **PostgreSQL StatefulSet** (3 replicas) with High Availability
- **Redis Deployment** (3 replicas) for caching
- **NGINX Ingress Controller** with security features
- **Monitoring Stack**: Prometheus, Grafana, Alertmanager
- **ConfigMaps & Secrets** for configuration management

## Directory Structure

```
k8s/
├── base/
│   └── namespace.yaml              # Namespace definition
├── database/
│   ├── postgresql-statefulset.yaml # PostgreSQL HA cluster
│   └── postgresql-service.yaml     # PostgreSQL services
├── cache/
│   ├── redis-deployment.yaml       # Redis cache deployment
│   └── redis-service.yaml          # Redis service
├── ingress/
│   ├── nginx-ingress-controller.yaml # NGINX ingress controller
│   └── ingress-rules.yaml          # Ingress routing rules
├── configmaps/
│   ├── postgres-config.yaml        # PostgreSQL configuration
│   ├── redis-config.yaml           # Redis configuration
│   └── app-config.yaml             # Application configuration
├── secrets/
│   ├── postgres-secret.yaml        # PostgreSQL credentials
│   ├── redis-secret.yaml           # Redis credentials
│   ├── app-secrets.yaml            # Application secrets
│   └── monitoring-auth.yaml        # Monitoring dashboard auth
└── monitoring/
    ├── prometheus/
    │   ├── prometheus-config.yaml  # Prometheus config & rules
    │   └── prometheus-deployment.yaml
    ├── grafana/
    │   ├── grafana-config.yaml     # Grafana datasources & dashboards
    │   └── grafana-deployment.yaml
    └── alertmanager/
        ├── alertmanager-config.yaml
        └── alertmanager-deployment.yaml
```

## Prerequisites

1. **Kubernetes Cluster** (v1.24+)
   - Minimum 3 nodes for HA setup
   - Node requirements:
     - 4 CPUs per node
     - 8GB RAM per node
     - 100GB storage per node

2. **kubectl** configured with cluster access

3. **StorageClass** named `fast-ssd` for persistent volumes
   ```bash
   kubectl get storageclass
   ```

4. **Cert-Manager** for TLS certificates (optional but recommended)
   ```bash
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
   ```

## Deployment Instructions

### 1. Update Secrets (CRITICAL!)

**IMPORTANT:** Before deploying, update all secrets with secure values!

```bash
# Generate secure passwords
openssl rand -base64 32

# Update secrets in:
# - k8s/secrets/postgres-secret.yaml
# - k8s/secrets/redis-secret.yaml
# - k8s/secrets/app-secrets.yaml
# - k8s/monitoring/grafana/grafana-deployment.yaml
```

### 2. Create Storage Class (if not exists)

```bash
cat <<EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs  # Change based on your cloud provider
parameters:
  type: gp3
  iopsPerGB: "10"
  fsType: ext4
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
EOF
```

### 3. Deploy Base Infrastructure

```bash
# Create namespace
kubectl apply -f base/namespace.yaml

# Apply ConfigMaps
kubectl apply -f configmaps/

# Apply Secrets (after updating them!)
kubectl apply -f secrets/
```

### 4. Deploy Database Layer

```bash
# Deploy PostgreSQL StatefulSet
kubectl apply -f database/postgresql-service.yaml
kubectl apply -f database/postgresql-statefulset.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgresql -n mentalhealth --timeout=300s

# Verify PostgreSQL
kubectl get statefulset postgresql -n mentalhealth
kubectl get pods -l app=postgresql -n mentalhealth
```

### 5. Deploy Cache Layer

```bash
# Deploy Redis
kubectl apply -f cache/redis-service.yaml
kubectl apply -f cache/redis-deployment.yaml

# Wait for Redis to be ready
kubectl wait --for=condition=ready pod -l app=redis -n mentalhealth --timeout=180s

# Verify Redis
kubectl get deployment redis -n mentalhealth
kubectl get pods -l app=redis -n mentalhealth
```

### 6. Deploy Ingress Controller

```bash
# Deploy NGINX Ingress Controller
kubectl apply -f ingress/nginx-ingress-controller.yaml

# Wait for ingress controller to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --timeout=300s

# Update domain names in ingress-rules.yaml, then apply
kubectl apply -f ingress/ingress-rules.yaml
```

### 7. Deploy Monitoring Stack

```bash
# Deploy Prometheus
kubectl apply -f monitoring/prometheus/prometheus-config.yaml
kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml

# Deploy Grafana
kubectl apply -f monitoring/grafana/grafana-config.yaml
kubectl apply -f monitoring/grafana/grafana-deployment.yaml

# Deploy Alertmanager
kubectl apply -f monitoring/alertmanager/alertmanager-config.yaml
kubectl apply -f monitoring/alertmanager/alertmanager-deployment.yaml

# Wait for monitoring stack to be ready
kubectl wait --for=condition=ready pod -l app=prometheus -n mentalhealth --timeout=180s
kubectl wait --for=condition=ready pod -l app=grafana -n mentalhealth --timeout=180s
```

## Verification

### Check All Resources

```bash
# Check namespace
kubectl get namespace mentalhealth

# Check all pods
kubectl get pods -n mentalhealth

# Check services
kubectl get svc -n mentalhealth

# Check persistent volume claims
kubectl get pvc -n mentalhealth

# Check ingress
kubectl get ingress -n mentalhealth
```

### Test Database Connection

```bash
# Connect to PostgreSQL
kubectl exec -it postgresql-0 -n mentalhealth -- psql -U postgres -d mentalhealth_db

# In psql:
\l              # List databases
\dt             # List tables
\q              # Quit
```

### Test Redis Connection

```bash
# Connect to Redis
kubectl exec -it deployment/redis -n mentalhealth -- redis-cli

# In redis-cli:
PING            # Should return PONG
INFO            # Show Redis info
EXIT            # Quit
```

### Access Monitoring Dashboards

```bash
# Port-forward Grafana (if not using ingress)
kubectl port-forward svc/grafana 3000:3000 -n mentalhealth

# Access at: http://localhost:3000
# Default credentials (CHANGE THESE!):
# Username: admin
# Password: CHANGE_ME_GRAFANA_PASSWORD

# Port-forward Prometheus
kubectl port-forward svc/prometheus 9090:9090 -n mentalhealth

# Access at: http://localhost:9090
```

## Monitoring & Observability

### Prometheus Metrics

- **URL**: https://prometheus.mentalhealth.example.com (via ingress)
- **Metrics collected**:
  - Kubernetes cluster metrics
  - Node metrics (CPU, memory, disk)
  - PostgreSQL metrics (connections, queries, replication)
  - Redis metrics (memory, commands, connections)
  - Ingress metrics (requests, latency)

### Grafana Dashboards

- **URL**: https://grafana.mentalhealth.example.com (via ingress)
- **Pre-configured dashboards**:
  - Kubernetes Cluster Overview
  - PostgreSQL Monitoring
  - Redis Monitoring
  - Application Metrics

### Alertmanager

- Configured alerts for:
  - High CPU/memory usage
  - Low disk space
  - Database connection issues
  - Redis memory pressure
  - Service downtime

## Scaling

### Scale PostgreSQL

```bash
# StatefulSet replicas (default: 3)
kubectl scale statefulset postgresql --replicas=5 -n mentalhealth
```

### Scale Redis

```bash
# Deployment replicas (default: 3)
kubectl scale deployment redis --replicas=5 -n mentalhealth
```

### Scale Ingress Controller

```bash
kubectl scale deployment nginx-ingress-controller --replicas=5 -n ingress-nginx
```

## Backup & Recovery

### PostgreSQL Backup

```bash
# Create backup
kubectl exec postgresql-0 -n mentalhealth -- pg_dump -U postgres mentalhealth_db > backup.sql

# Restore backup
kubectl exec -i postgresql-0 -n mentalhealth -- psql -U postgres -d mentalhealth_db < backup.sql
```

### Redis Backup

```bash
# Trigger RDB snapshot
kubectl exec deployment/redis -n mentalhealth -- redis-cli BGSAVE

# Copy snapshot
kubectl cp mentalhealth/redis-pod:/data/dump.rdb ./redis-backup.rdb
```

## Troubleshooting

### Check Pod Logs

```bash
# PostgreSQL logs
kubectl logs -f postgresql-0 -n mentalhealth

# Redis logs
kubectl logs -f deployment/redis -n mentalhealth

# Ingress controller logs
kubectl logs -f deployment/nginx-ingress-controller -n ingress-nginx
```

### Common Issues

#### 1. Pods stuck in Pending
```bash
# Check events
kubectl describe pod <pod-name> -n mentalhealth

# Common causes:
# - Insufficient resources
# - StorageClass not available
# - PVC not bound
```

#### 2. Database connection failures
```bash
# Check PostgreSQL status
kubectl exec postgresql-0 -n mentalhealth -- pg_isready

# Check secrets
kubectl get secret postgres-secret -n mentalhealth -o yaml
```

#### 3. Ingress not accessible
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress rules
kubectl describe ingress mentalhealth-ingress -n mentalhealth

# Check LoadBalancer IP
kubectl get svc ingress-nginx -n ingress-nginx
```

## Security Considerations

1. **Secrets Management**
   - Never commit actual secrets to version control
   - Use sealed secrets or external secret managers in production
   - Rotate secrets regularly

2. **Network Policies**
   - Implement network policies to restrict pod-to-pod communication
   - Only allow necessary traffic

3. **RBAC**
   - Follow principle of least privilege
   - Use separate service accounts for different components

4. **TLS/SSL**
   - Enable TLS for all external endpoints
   - Use cert-manager for automatic certificate management

5. **Pod Security**
   - Run containers as non-root users
   - Enable Pod Security Standards (PSS)

## Maintenance

### Update Container Images

```bash
# Update PostgreSQL
kubectl set image statefulset/postgresql postgresql=postgres:15-alpine -n mentalhealth

# Update Redis
kubectl set image deployment/redis redis=redis:7-alpine -n mentalhealth

# Update Prometheus
kubectl set image deployment/prometheus prometheus=prom/prometheus:v2.48.0 -n mentalhealth
```

### Rolling Updates

```bash
# Update with zero downtime
kubectl rollout restart deployment/redis -n mentalhealth
kubectl rollout status deployment/redis -n mentalhealth
```

## Clean Up

```bash
# Delete all resources in namespace
kubectl delete namespace mentalhealth

# Delete ingress controller
kubectl delete namespace ingress-nginx
```

## Production Checklist

- [ ] Update all secrets with strong, random passwords
- [ ] Configure proper domain names in ingress rules
- [ ] Set up TLS certificates (cert-manager or manual)
- [ ] Configure email/Slack for Alertmanager notifications
- [ ] Set up proper backup strategy for databases
- [ ] Configure resource limits based on load testing
- [ ] Implement network policies
- [ ] Enable Pod Security Standards
- [ ] Set up log aggregation (ELK/Loki)
- [ ] Configure horizontal pod autoscaling (HPA)
- [ ] Set up disaster recovery plan
- [ ] Document runbooks for common issues

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [PostgreSQL on Kubernetes](https://www.postgresql.org/docs/)
- [Redis Best Practices](https://redis.io/docs/management/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Prometheus Operator](https://prometheus-operator.dev/)

## Support

For issues or questions:
- Check logs: `kubectl logs -n mentalhealth <pod-name>`
- Check events: `kubectl get events -n mentalhealth`
- Check documentation: [Project Wiki](https://github.com/your-org/mentalhealth/wiki)
