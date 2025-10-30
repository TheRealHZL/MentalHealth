#!/bin/bash

# MentalHealth Platform - Kubernetes Deployment Script
# This script automatically deploys the entire platform to Kubernetes

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
DOCKER_REGISTRY="${DOCKER_REGISTRY:-ghcr.io/therealHZL}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}MentalHealth Platform - K8s Deployment${NC}"
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
    print_info "Visit: https://kubernetes.io/docs/tasks/tools/"
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

# Show cluster info
CLUSTER_NAME=$(kubectl config current-context)
print_info "Using cluster: ${CLUSTER_NAME}"

# Navigate to k8s directory
cd "$K8S_DIR"

# Create namespace
print_info "Creating namespace: ${NAMESPACE}..."
kubectl apply -f base/namespace.yaml
print_success "Namespace created"

# Create secrets
print_info "Creating secrets..."
print_warning "Please ensure you have updated secrets in k8s/secrets/app-secrets.yaml"

# Generate secrets if not exists
if [ ! -f secrets/app-secrets-generated.yaml ]; then
    print_info "Generating secrets..."

    # Generate random passwords
    DB_PASSWORD=$(openssl rand -base64 32)
    REDIS_PASSWORD=$(openssl rand -base64 32)
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET_KEY=$(openssl rand -hex 32)

    cat > secrets/app-secrets-generated.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  # Database credentials
  DATABASE_USER: mentalhealth
  DATABASE_PASSWORD: ${DB_PASSWORD}
  DATABASE_NAME: mentalhealth_db
  DATABASE_HOST: postgresql-service
  DATABASE_PORT: "5432"

  # Redis credentials
  REDIS_PASSWORD: ${REDIS_PASSWORD}

  # Security keys
  SECRET_KEY: ${SECRET_KEY}
  JWT_SECRET_KEY: ${JWT_SECRET_KEY}
  JWT_ALGORITHM: HS256
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"

  # AI Configuration (uses custom PyTorch models)
  AI_DEVICE: cpu

  # Application
  DEBUG: "false"
  LOG_LEVEL: info
  ENVIRONMENT: production
  CORS_ORIGINS: http://localhost:3000,http://localhost:8000
EOF
    print_success "Secrets generated"
fi

kubectl apply -f secrets/app-secrets-generated.yaml
print_success "Secrets applied"

# Create ConfigMaps
print_info "Creating ConfigMaps..."
kubectl apply -f config/postgresql-config.yaml
kubectl apply -f config/redis-config.yaml
kubectl apply -f config/app-config.yaml
print_success "ConfigMaps created"

# Create Storage Class
print_info "Creating Storage Class..."
kubectl apply -f base/storage-class.yaml || print_warning "Storage class may already exist"
print_success "Storage Class configured"

# Create Network Policies
print_info "Applying Network Policies..."
kubectl apply -f base/network-policy.yaml
print_success "Network Policies applied"

# Deploy PostgreSQL
print_info "Deploying PostgreSQL StatefulSet..."
kubectl apply -f database/postgresql-service.yaml
kubectl apply -f database/postgresql-statefulset.yaml
print_success "PostgreSQL deployment started"

# Wait for PostgreSQL to be ready
print_info "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgresql -n ${NAMESPACE} --timeout=300s || {
    print_warning "PostgreSQL pods not ready yet, continuing..."
}
print_success "PostgreSQL is ready"

# Deploy Redis
print_info "Deploying Redis..."
kubectl apply -f cache/redis-service.yaml
kubectl apply -f cache/redis-deployment.yaml
print_success "Redis deployment started"

# Wait for Redis to be ready
print_info "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n ${NAMESPACE} --timeout=300s || {
    print_warning "Redis pods not ready yet, continuing..."
}
print_success "Redis is ready"

# Deploy Backend
print_info "Deploying Backend application..."
kubectl apply -f app/backend-service.yaml
kubectl apply -f app/backend-deployment.yaml
kubectl apply -f app/backend-hpa.yaml
print_success "Backend deployment started"

# Wait for Backend to be ready
print_info "Waiting for Backend to be ready..."
kubectl wait --for=condition=ready pod -l app=backend -n ${NAMESPACE} --timeout=300s || {
    print_warning "Backend pods not ready yet, continuing..."
}
print_success "Backend is ready"

# Deploy Frontend
print_info "Deploying Frontend application..."
kubectl apply -f app/frontend-service.yaml
kubectl apply -f app/frontend-deployment.yaml
kubectl apply -f app/frontend-hpa.yaml
print_success "Frontend deployment started"

# Wait for Frontend to be ready
print_info "Waiting for Frontend to be ready..."
kubectl wait --for=condition=ready pod -l app=frontend -n ${NAMESPACE} --timeout=300s || {
    print_warning "Frontend pods not ready yet, continuing..."
}
print_success "Frontend is ready"

# Deploy Ingress Controller
print_info "Deploying NGINX Ingress Controller..."
kubectl apply -f ingress/nginx-ingress-controller.yaml
kubectl apply -f ingress/ingress.yaml
print_success "Ingress Controller deployed"

# Deploy Monitoring (optional)
read -p "$(echo -e ${YELLOW}Do you want to deploy monitoring stack? [y/N]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Deploying Monitoring Stack..."

    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

    # Deploy Prometheus
    print_info "Deploying Prometheus..."
    kubectl apply -f monitoring/prometheus/

    # Deploy Grafana
    print_info "Deploying Grafana..."
    kubectl apply -f monitoring/grafana/

    # Deploy Alertmanager
    print_info "Deploying Alertmanager..."
    kubectl apply -f monitoring/alertmanager/

    print_success "Monitoring stack deployed"
else
    print_info "Skipping monitoring stack deployment"
fi

# Show deployment status
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Deployment Status${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

print_info "Pods in ${NAMESPACE} namespace:"
kubectl get pods -n ${NAMESPACE}

echo ""
print_info "Services in ${NAMESPACE} namespace:"
kubectl get svc -n ${NAMESPACE}

echo ""
print_info "Ingress in ${NAMESPACE} namespace:"
kubectl get ingress -n ${NAMESPACE}

# Get service URLs
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""

# Get LoadBalancer IPs
BACKEND_IP=$(kubectl get svc backend-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
FRONTEND_IP=$(kubectl get svc frontend-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
INGRESS_IP=$(kubectl get svc nginx-ingress-controller -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

echo -e "${GREEN}Access the application at:${NC}"
if [ "$INGRESS_IP" != "pending" ]; then
    echo -e "  Application: ${BLUE}http://${INGRESS_IP}${NC}"
    echo -e "  API:         ${BLUE}http://${INGRESS_IP}/api${NC}"
else
    echo -e "  Frontend:    ${BLUE}http://${FRONTEND_IP}:3000${NC} (LoadBalancer pending)"
    echo -e "  Backend:     ${BLUE}http://${BACKEND_IP}:8000${NC} (LoadBalancer pending)"
fi

echo ""
echo -e "${YELLOW}Note:${NC} If using LoadBalancer type services, IPs may take a few minutes to be assigned."
echo -e "${YELLOW}Note:${NC} For local clusters (minikube/kind), use port-forward instead:"
echo ""
echo -e "${BLUE}Port forwarding commands:${NC}"
echo -e "  Frontend:  ${YELLOW}kubectl port-forward -n ${NAMESPACE} svc/frontend-service 3000:3000${NC}"
echo -e "  Backend:   ${YELLOW}kubectl port-forward -n ${NAMESPACE} svc/backend-service 8000:8000${NC}"
echo ""

echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View pods:          ${YELLOW}kubectl get pods -n ${NAMESPACE}${NC}"
echo -e "  View logs:          ${YELLOW}kubectl logs -f -n ${NAMESPACE} <pod-name>${NC}"
echo -e "  Describe pod:       ${YELLOW}kubectl describe pod -n ${NAMESPACE} <pod-name>${NC}"
echo -e "  Exec into pod:      ${YELLOW}kubectl exec -it -n ${NAMESPACE} <pod-name> -- /bin/bash${NC}"
echo -e "  Scale deployment:   ${YELLOW}kubectl scale deployment -n ${NAMESPACE} <deployment-name> --replicas=3${NC}"
echo -e "  Delete deployment:  ${YELLOW}kubectl delete all -n ${NAMESPACE} --all${NC}"
echo ""
