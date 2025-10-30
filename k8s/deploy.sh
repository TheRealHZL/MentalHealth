#!/bin/bash

# MentalHealth Kubernetes Deployment Script
# This script helps deploy the entire infrastructure to Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl first."
        exit 1
    fi

    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please configure kubectl."
        exit 1
    fi

    log_info "Prerequisites check passed!"
}

check_secrets() {
    log_warn "IMPORTANT: Have you updated all secrets with secure values?"
    log_warn "Files to update:"
    log_warn "  - secrets/postgres-secret.yaml"
    log_warn "  - secrets/redis-secret.yaml"
    log_warn "  - secrets/app-secrets.yaml"
    log_warn "  - monitoring/grafana/grafana-deployment.yaml"

    read -p "Have you updated all secrets? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
        log_error "Please update secrets before deploying!"
        exit 1
    fi
}

deploy_base() {
    log_info "Deploying base infrastructure..."

    # Create namespace
    kubectl apply -f base/namespace.yaml

    # Create storage class
    kubectl apply -f base/storageclass.yaml

    # Apply network policies
    kubectl apply -f base/network-policy.yaml

    log_info "Base infrastructure deployed!"
}

deploy_config() {
    log_info "Deploying configuration..."

    # Apply ConfigMaps
    kubectl apply -f configmaps/

    # Apply Secrets
    kubectl apply -f secrets/

    log_info "Configuration deployed!"
}

deploy_database() {
    log_info "Deploying PostgreSQL..."

    kubectl apply -f database/postgresql-service.yaml
    kubectl apply -f database/postgresql-statefulset.yaml

    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgresql -n mentalhealth --timeout=300s || log_warn "PostgreSQL is taking longer than expected"

    log_info "PostgreSQL deployed!"
}

deploy_cache() {
    log_info "Deploying Redis..."

    kubectl apply -f cache/redis-service.yaml
    kubectl apply -f cache/redis-deployment.yaml

    log_info "Waiting for Redis to be ready..."
    kubectl wait --for=condition=ready pod -l app=redis -n mentalhealth --timeout=180s || log_warn "Redis is taking longer than expected"

    log_info "Redis deployed!"
}

deploy_ingress() {
    log_info "Deploying NGINX Ingress Controller..."

    kubectl apply -f ingress/nginx-ingress-controller.yaml

    log_info "Waiting for Ingress Controller to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx --timeout=300s || log_warn "Ingress controller is taking longer than expected"

    log_warn "Please update domain names in ingress/ingress-rules.yaml before applying ingress rules!"
    read -p "Apply ingress rules now? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy]es$ ]]; then
        kubectl apply -f ingress/ingress-rules.yaml
    fi

    log_info "Ingress Controller deployed!"
}

deploy_monitoring() {
    log_info "Deploying Monitoring Stack..."

    # Prometheus
    kubectl apply -f monitoring/prometheus/prometheus-config.yaml
    kubectl apply -f monitoring/prometheus/prometheus-deployment.yaml

    # Grafana
    kubectl apply -f monitoring/grafana/grafana-config.yaml
    kubectl apply -f monitoring/grafana/grafana-deployment.yaml

    # Alertmanager
    kubectl apply -f monitoring/alertmanager/alertmanager-config.yaml
    kubectl apply -f monitoring/alertmanager/alertmanager-deployment.yaml

    log_info "Waiting for monitoring stack to be ready..."
    kubectl wait --for=condition=ready pod -l app=prometheus -n mentalhealth --timeout=180s || log_warn "Prometheus is taking longer than expected"
    kubectl wait --for=condition=ready pod -l app=grafana -n mentalhealth --timeout=180s || log_warn "Grafana is taking longer than expected"

    log_info "Monitoring Stack deployed!"
}

show_status() {
    log_info "Deployment Status:"
    echo ""

    log_info "Namespaces:"
    kubectl get namespace mentalhealth ingress-nginx
    echo ""

    log_info "Pods:"
    kubectl get pods -n mentalhealth
    echo ""

    log_info "Services:"
    kubectl get svc -n mentalhealth
    echo ""

    log_info "Persistent Volume Claims:"
    kubectl get pvc -n mentalhealth
    echo ""

    log_info "Ingress:"
    kubectl get ingress -n mentalhealth
    echo ""

    log_info "Ingress Controller External IP:"
    kubectl get svc ingress-nginx -n ingress-nginx
}

# Main deployment flow
main() {
    echo "========================================="
    echo "MentalHealth Kubernetes Deployment"
    echo "========================================="
    echo ""

    check_prerequisites
    check_secrets

    echo ""
    log_info "Starting deployment..."
    echo ""

    deploy_base
    sleep 2

    deploy_config
    sleep 2

    deploy_database
    sleep 5

    deploy_cache
    sleep 3

    deploy_ingress
    sleep 3

    deploy_monitoring
    sleep 3

    echo ""
    log_info "Deployment completed!"
    echo ""

    show_status

    echo ""
    log_info "Next steps:"
    log_warn "1. Verify all pods are running: kubectl get pods -n mentalhealth"
    log_warn "2. Access Grafana: kubectl port-forward svc/grafana 3000:3000 -n mentalhealth"
    log_warn "3. Access Prometheus: kubectl port-forward svc/prometheus 9090:9090 -n mentalhealth"
    log_warn "4. Check logs if any pod is not running: kubectl logs <pod-name> -n mentalhealth"
    log_warn "5. Update DNS records to point to the LoadBalancer IP"
}

# Run main function
main
