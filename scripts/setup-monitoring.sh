#!/bin/bash

# MentalHealth Platform - Monitoring Setup Script
# This script sets up Prometheus, Grafana, and Alertmanager for monitoring

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
K8S_DIR="$PROJECT_ROOT/k8s"

# Configuration
NAMESPACE="mentalhealth"
MONITORING_NAMESPACE="monitoring"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}MentalHealth - Monitoring Setup${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is installed
print_info "Checking kubectl installation..."
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed. Please install kubectl first."
    exit 1
fi
print_success "kubectl is installed"

# Check cluster connection
print_info "Checking Kubernetes cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi
print_success "Connected to Kubernetes cluster"

# Create monitoring namespace
print_info "Creating monitoring namespace..."
kubectl create namespace ${MONITORING_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
print_success "Monitoring namespace created"

# Navigate to k8s directory
cd "$K8S_DIR"

# Deploy Prometheus
echo ""
print_info "Deploying Prometheus..."

# Create Prometheus ConfigMap
print_info "Creating Prometheus configuration..."
kubectl apply -f monitoring/prometheus/prometheus-config.yaml
print_success "Prometheus ConfigMap created"

# Create Prometheus RBAC
print_info "Creating Prometheus RBAC..."
kubectl apply -f monitoring/prometheus/prometheus-rbac.yaml
print_success "Prometheus RBAC created"

# Deploy Prometheus
print_info "Deploying Prometheus server..."
kubectl apply -f monitoring/prometheus/prometheus-service.yaml
kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml
print_success "Prometheus deployed"

# Wait for Prometheus
print_info "Waiting for Prometheus to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus -n ${MONITORING_NAMESPACE} --timeout=300s || {
    print_warning "Prometheus pods not ready yet, continuing..."
}
print_success "Prometheus is ready"

# Deploy Grafana
echo ""
print_info "Deploying Grafana..."

# Create Grafana ConfigMaps
print_info "Creating Grafana configuration..."
kubectl apply -f monitoring/grafana/grafana-config.yaml
kubectl apply -f monitoring/grafana/grafana-dashboards.yaml
print_success "Grafana ConfigMaps created"

# Deploy Grafana
print_info "Deploying Grafana server..."
kubectl apply -f monitoring/grafana/grafana-service.yaml
kubectl apply -f monitoring/grafana/grafana-deployment.yaml
print_success "Grafana deployed"

# Wait for Grafana
print_info "Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod -l app=grafana -n ${MONITORING_NAMESPACE} --timeout=300s || {
    print_warning "Grafana pods not ready yet, continuing..."
}
print_success "Grafana is ready"

# Deploy Alertmanager
echo ""
print_info "Deploying Alertmanager..."

# Create Alertmanager ConfigMap
print_info "Creating Alertmanager configuration..."
kubectl apply -f monitoring/alertmanager/alertmanager-config.yaml
print_success "Alertmanager ConfigMap created"

# Deploy Alertmanager
print_info "Deploying Alertmanager server..."
kubectl apply -f monitoring/alertmanager/alertmanager-service.yaml
kubectl apply -f monitoring/alertmanager/alertmanager-deployment.yaml
print_success "Alertmanager deployed"

# Wait for Alertmanager
print_info "Waiting for Alertmanager to be ready..."
kubectl wait --for=condition=ready pod -l app=alertmanager -n ${MONITORING_NAMESPACE} --timeout=300s || {
    print_warning "Alertmanager pods not ready yet, continuing..."
}
print_success "Alertmanager is ready"

# Create ServiceMonitors for automatic discovery
echo ""
print_info "Creating ServiceMonitors..."

# Create ServiceMonitor for Backend
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: backend-monitor
  namespace: ${NAMESPACE}
  labels:
    app: backend
spec:
  selector:
    matchLabels:
      app: backend
  endpoints:
  - port: http
    path: /metrics
    interval: 30s
EOF
print_success "Backend ServiceMonitor created"

# Create ServiceMonitor for PostgreSQL
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: postgresql-monitor
  namespace: ${NAMESPACE}
  labels:
    app: postgresql
spec:
  selector:
    matchLabels:
      app: postgresql
  endpoints:
  - port: metrics
    interval: 30s
EOF
print_success "PostgreSQL ServiceMonitor created"

# Create ServiceMonitor for Redis
cat <<EOF | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: redis-monitor
  namespace: ${NAMESPACE}
  labels:
    app: redis
spec:
  selector:
    matchLabels:
      app: redis
  endpoints:
  - port: metrics
    interval: 30s
EOF
print_success "Redis ServiceMonitor created"

# Show deployment status
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Monitoring Status${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

print_info "Pods in ${MONITORING_NAMESPACE} namespace:"
kubectl get pods -n ${MONITORING_NAMESPACE}

echo ""
print_info "Services in ${MONITORING_NAMESPACE} namespace:"
kubectl get svc -n ${MONITORING_NAMESPACE}

# Get service URLs
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Monitoring Setup Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Get LoadBalancer IPs or use port-forward
PROMETHEUS_IP=$(kubectl get svc prometheus-service -n ${MONITORING_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
GRAFANA_IP=$(kubectl get svc grafana-service -n ${MONITORING_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
ALERTMANAGER_IP=$(kubectl get svc alertmanager-service -n ${MONITORING_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

echo -e "${GREEN}Access monitoring dashboards:${NC}"
echo ""

if [ -n "$PROMETHEUS_IP" ]; then
    echo -e "  Prometheus:   ${BLUE}http://${PROMETHEUS_IP}:9090${NC}"
else
    echo -e "  Prometheus:   ${YELLOW}kubectl port-forward -n ${MONITORING_NAMESPACE} svc/prometheus-service 9090:9090${NC}"
    echo -e "                ${BLUE}http://localhost:9090${NC}"
fi

echo ""
if [ -n "$GRAFANA_IP" ]; then
    echo -e "  Grafana:      ${BLUE}http://${GRAFANA_IP}:3001${NC}"
else
    echo -e "  Grafana:      ${YELLOW}kubectl port-forward -n ${MONITORING_NAMESPACE} svc/grafana-service 3001:3000${NC}"
    echo -e "                ${BLUE}http://localhost:3001${NC}"
fi

echo ""
if [ -n "$ALERTMANAGER_IP" ]; then
    echo -e "  Alertmanager: ${BLUE}http://${ALERTMANAGER_IP}:9093${NC}"
else
    echo -e "  Alertmanager: ${YELLOW}kubectl port-forward -n ${MONITORING_NAMESPACE} svc/alertmanager-service 9093:9093${NC}"
    echo -e "                ${BLUE}http://localhost:9093${NC}"
fi

echo ""
echo -e "${YELLOW}Grafana default credentials:${NC}"
echo -e "  Username: ${BLUE}admin${NC}"
echo -e "  Password: ${BLUE}admin${NC}"
echo -e "  ${RED}Please change the password after first login!${NC}"
echo ""

echo -e "${BLUE}Available Grafana Dashboards:${NC}"
echo -e "  - Application Metrics"
echo -e "  - PostgreSQL Metrics"
echo -e "  - Redis Metrics"
echo -e "  - Kubernetes Cluster Metrics"
echo -e "  - AI Training Metrics"
echo ""

echo -e "${BLUE}Prometheus Targets:${NC}"
echo -e "  Check targets status at: ${YELLOW}Prometheus → Status → Targets${NC}"
echo ""

echo -e "${GREEN}Monitoring stack is now collecting metrics!${NC}"
echo -e "  - Backend metrics:     ${YELLOW}http://<backend-ip>:8000/metrics${NC}"
echo -e "  - PostgreSQL metrics:  ${YELLOW}Prometheus will scrape automatically${NC}"
echo -e "  - Redis metrics:       ${YELLOW}Prometheus will scrape automatically${NC}"
echo ""

echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View Prometheus logs:   ${YELLOW}kubectl logs -f -n ${MONITORING_NAMESPACE} -l app=prometheus${NC}"
echo -e "  View Grafana logs:      ${YELLOW}kubectl logs -f -n ${MONITORING_NAMESPACE} -l app=grafana${NC}"
echo -e "  Restart Prometheus:     ${YELLOW}kubectl rollout restart deployment/prometheus-deployment -n ${MONITORING_NAMESPACE}${NC}"
echo -e "  Restart Grafana:        ${YELLOW}kubectl rollout restart deployment/grafana-deployment -n ${MONITORING_NAMESPACE}${NC}"
echo ""
