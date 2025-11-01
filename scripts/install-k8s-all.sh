#!/bin/bash

# MentalHealth Platform - Complete Kubernetes Installation
# This script installs kubectl, sets up a Kubernetes cluster (minikube/kind), and deploys the platform
# Run with: curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-k8s-all.sh | bash

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/TheRealHZL/MentalHealth.git"
INSTALL_DIR="$HOME/MentalHealth"
BRANCH="main"
NAMESPACE="mentalhealth"

echo -e "${MAGENTA}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     MentalHealth Platform - Kubernetes Installation          ║
║                                                               ║
║   This script will set up a complete Kubernetes cluster      ║
║   and deploy the MentalHealth Platform.                      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
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

print_step() {
    echo ""
    echo -e "${CYAN}===================================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}===================================================${NC}"
}

# Detect OS
print_step "Step 1: Detecting Operating System"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
    print_info "Detected OS: $OS $VER"
elif [ "$(uname)" == "Darwin" ]; then
    OS="macos"
    print_info "Detected OS: macOS"
else
    print_error "Unable to detect operating system"
    exit 1
fi

print_success "Operating system detected"

# Install kubectl
print_step "Step 2: Installing kubectl"

install_kubectl() {
    if command -v kubectl &> /dev/null; then
        print_info "kubectl is already installed"
        kubectl version --client
    else
        print_info "Installing kubectl..."

        case $OS in
            ubuntu|debian)
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates curl
                curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
                echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
                sudo apt-get update
                sudo apt-get install -y kubectl
                ;;

            centos|rhel|fedora)
                cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://pkgs.k8s.io/core:/stable:/v1.28/rpm/
enabled=1
gpgcheck=1
gpgkey=https://pkgs.k8s.io/core:/stable:/v1.28/rpm/repodata/repomd.xml.key
EOF
                sudo yum install -y kubectl
                ;;

            macos)
                if ! command -v brew &> /dev/null; then
                    print_error "Homebrew is required for macOS. Please install it first."
                    exit 1
                fi
                brew install kubectl
                ;;
        esac

        print_success "kubectl installed"
    fi
}

install_kubectl

# Install Docker (needed for minikube/kind)
print_step "Step 3: Installing Docker"

install_docker() {
    if command -v docker &> /dev/null; then
        print_info "Docker is already installed"
        docker --version
    else
        print_info "Installing Docker..."

        case $OS in
            ubuntu|debian)
                sudo mkdir -p /etc/apt/keyrings
                curl -fsSL https://download.docker.com/linux/$OS/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                echo \
                  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/$OS \
                  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io
                sudo usermod -aG docker $USER
                ;;

            centos|rhel|fedora)
                sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                sudo yum install -y docker-ce docker-ce-cli containerd.io
                sudo systemctl start docker
                sudo systemctl enable docker
                sudo usermod -aG docker $USER
                ;;

            macos)
                brew install --cask docker
                print_warning "Please start Docker Desktop manually"
                ;;
        esac

        print_success "Docker installed"
    fi
}

install_docker

# Start Docker if not running
if [ "$OS" != "macos" ]; then
    if ! sudo systemctl is-active --quiet docker; then
        sudo systemctl start docker
    fi
fi

# Choose Kubernetes cluster type
print_step "Step 4: Kubernetes Cluster Setup"

echo ""
print_info "Choose your Kubernetes cluster option:"
echo ""
echo "  1) Use existing cluster (kubectl already configured)"
echo "  2) Install and use minikube (recommended for local testing)"
echo "  3) Install and use kind (Kubernetes in Docker)"
echo ""
read -p "Enter your choice (1-3): " CLUSTER_CHOICE

case $CLUSTER_CHOICE in
    1)
        print_info "Using existing Kubernetes cluster..."
        if ! kubectl cluster-info &> /dev/null; then
            print_error "Cannot connect to Kubernetes cluster. Please configure kubectl first."
            exit 1
        fi
        print_success "Connected to existing cluster"
        CLUSTER_CONTEXT=$(kubectl config current-context)
        print_info "Using context: $CLUSTER_CONTEXT"
        ;;

    2)
        print_info "Installing minikube..."

        if ! command -v minikube &> /dev/null; then
            case $OS in
                ubuntu|debian)
                    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
                    sudo install minikube-linux-amd64 /usr/local/bin/minikube
                    rm minikube-linux-amd64
                    ;;
                macos)
                    brew install minikube
                    ;;
                *)
                    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
                    sudo install minikube-linux-amd64 /usr/local/bin/minikube
                    rm minikube-linux-amd64
                    ;;
            esac
        fi

        print_info "Starting minikube cluster..."
        minikube start --cpus=4 --memory=8192 --driver=docker
        print_success "Minikube cluster started"
        ;;

    3)
        print_info "Installing kind..."

        if ! command -v kind &> /dev/null; then
            case $OS in
                ubuntu|debian|centos|rhel|fedora)
                    curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
                    chmod +x ./kind
                    sudo mv ./kind /usr/local/bin/kind
                    ;;
                macos)
                    brew install kind
                    ;;
            esac
        fi

        print_info "Creating kind cluster..."
        cat <<EOF | kind create cluster --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
- role: worker
EOF
        print_success "Kind cluster created"
        ;;

    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Verify cluster connection
print_info "Verifying cluster connection..."
kubectl cluster-info
print_success "Cluster is accessible"

# Install Git
print_step "Step 5: Installing Git"

if ! command -v git &> /dev/null; then
    case $OS in
        ubuntu|debian)
            sudo apt-get install -y git
            ;;
        centos|rhel|fedora)
            sudo yum install -y git
            ;;
        macos)
            brew install git
            ;;
    esac
fi
print_success "Git is installed"

# Clone repository
print_step "Step 6: Cloning Repository"

if [ -d "$INSTALL_DIR" ]; then
    print_warning "Directory $INSTALL_DIR already exists"
    read -p "Remove and clone fresh? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$INSTALL_DIR"
    else
        cd "$INSTALL_DIR"
        git pull origin $BRANCH
    fi
fi

if [ ! -d "$INSTALL_DIR" ]; then
    git clone -b $BRANCH $REPO_URL "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
print_success "Repository ready"

# Create namespace
print_step "Step 7: Creating Kubernetes Namespace"

kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
print_success "Namespace created"

# Generate secrets
print_step "Step 8: Generating Secrets"

DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
REDIS_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

cat > k8s/secrets/app-secrets-generated.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  DATABASE_USER: mentalhealth
  DATABASE_PASSWORD: ${DB_PASSWORD}
  DATABASE_NAME: mentalhealth_db
  DATABASE_HOST: postgresql-service
  DATABASE_PORT: "5432"
  REDIS_PASSWORD: ${REDIS_PASSWORD}
  SECRET_KEY: ${SECRET_KEY}
  JWT_SECRET_KEY: ${JWT_SECRET_KEY}
  JWT_ALGORITHM: HS256
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"
  AI_DEVICE: cpu
  DEBUG: "false"
  LOG_LEVEL: info
  ENVIRONMENT: production
  CORS_ORIGINS: http://localhost:3000,http://localhost:8080
EOF

kubectl apply -f k8s/secrets/app-secrets-generated.yaml
print_success "Secrets created"

# Deploy platform
print_step "Step 9: Deploying Platform Components"

print_info "Deploying ConfigMaps..."
kubectl apply -f k8s/config/
print_success "ConfigMaps deployed"

print_info "Deploying Storage..."
kubectl apply -f k8s/base/storage-class.yaml || true
print_success "Storage configured"

print_info "Deploying Network Policies..."
kubectl apply -f k8s/base/network-policy.yaml
print_success "Network policies applied"

print_info "Deploying PostgreSQL..."
kubectl apply -f k8s/database/
print_success "PostgreSQL deployed"

print_info "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgresql -n ${NAMESPACE} --timeout=300s || true
print_success "PostgreSQL is ready"

print_info "Deploying Redis..."
kubectl apply -f k8s/cache/
print_success "Redis deployed"

print_info "Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n ${NAMESPACE} --timeout=300s || true
print_success "Redis is ready"

print_info "Deploying Backend..."
kubectl apply -f k8s/app/backend-deployment.yaml
kubectl apply -f k8s/app/backend-service.yaml
kubectl apply -f k8s/app/backend-hpa.yaml
print_success "Backend deployed"

print_info "Waiting for Backend to be ready..."
kubectl wait --for=condition=ready pod -l app=backend -n ${NAMESPACE} --timeout=300s || true
print_success "Backend is ready"

print_info "Deploying Frontend..."
kubectl apply -f k8s/app/frontend-deployment.yaml
kubectl apply -f k8s/app/frontend-service.yaml
kubectl apply -f k8s/app/frontend-hpa.yaml
print_success "Frontend deployed"

print_info "Deploying Ingress..."
kubectl apply -f k8s/ingress/ || true
print_success "Ingress configured"

# Get admin credentials
print_step "Step 10: Admin User Setup"

echo ""
read -p "Admin email [admin@mentalhealth.com]: " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@mentalhealth.com}

read -p "Admin username [admin]: " ADMIN_USERNAME
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}

read -s -p "Admin password [admin123]: " ADMIN_PASSWORD
echo ""
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

# Wait for backend pod
print_info "Waiting for backend pod..."
sleep 10

BACKEND_POD=$(kubectl get pods -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].metadata.name}')

if [ -z "$BACKEND_POD" ]; then
    print_warning "Backend pod not found yet. You can create admin user later with:"
    print_info "kubectl exec -n ${NAMESPACE} \$(kubectl get pods -n ${NAMESPACE} -l app=backend -o jsonpath='{.items[0].metadata.name}') -- python /tmp/create_admin.py"
else
    print_info "Creating admin user..."

    CREATE_ADMIN_SCRIPT="
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.models.user import User
from src.core.security import get_password_hash

async def create_admin():
    database_url = 'postgresql+asyncpg://mentalhealth:${DB_PASSWORD}@postgresql-service:5432/mentalhealth_db'
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            result = await session.execute(select(User).where(User.email == '${ADMIN_EMAIL}'))
            if result.scalar_one_or_none():
                print('Admin already exists')
                return

            admin = User(
                email='${ADMIN_EMAIL}',
                username='${ADMIN_USERNAME}',
                hashed_password=get_password_hash('${ADMIN_PASSWORD}'),
                role='admin',
                is_active=True,
                is_verified=True
            )
            session.add(admin)
            await session.commit()
            print('Admin created!')
        except Exception as e:
            print(f'Error: {e}')
        finally:
            await engine.dispose()

asyncio.run(create_admin())
"

    echo "$CREATE_ADMIN_SCRIPT" | kubectl exec -i -n ${NAMESPACE} ${BACKEND_POD} -- python -c "$(cat)"
    print_success "Admin user created"
fi

# Installation complete
print_step "Installation Complete!"

echo ""
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║           🎉 Kubernetes Deployment Complete! 🎉               ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

echo -e "${GREEN}Your MentalHealth Platform is running on Kubernetes!${NC}"
echo ""

# Get service info
FRONTEND_IP=$(kubectl get svc frontend-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
BACKEND_IP=$(kubectl get svc backend-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")

if [ -n "$FRONTEND_IP" ] && [ "$FRONTEND_IP" != "null" ]; then
    echo -e "  🌐 Frontend:  ${CYAN}http://${FRONTEND_IP}${NC}"
    echo -e "  🔧 Backend:   ${CYAN}http://${BACKEND_IP}${NC}"
else
    echo -e "${YELLOW}Using port-forwarding for access:${NC}"
    echo ""
    echo -e "  Run these commands in separate terminals:"
    echo ""
    echo -e "  ${CYAN}kubectl port-forward -n ${NAMESPACE} svc/frontend-service 3000:3000${NC}"
    echo -e "  ${CYAN}kubectl port-forward -n ${NAMESPACE} svc/backend-service 8000:8080${NC}"
    echo ""
    echo -e "  Then access:"
    echo -e "  🌐 Frontend:  ${CYAN}http://localhost:3000${NC}"
    echo -e "  🔧 Backend:   ${CYAN}http://localhost:8080${NC}"
    echo -e "  📚 API Docs:  ${CYAN}http://localhost:8080/docs${NC}"
    echo -e "  👑 Admin:     ${CYAN}http://localhost:3000/admin${NC}"
fi

echo ""
echo -e "${YELLOW}Admin Credentials:${NC}"
echo -e "  📧 Email:    ${CYAN}${ADMIN_EMAIL}${NC}"
echo -e "  👤 Username: ${CYAN}${ADMIN_USERNAME}${NC}"
echo -e "  🔑 Password: ${CYAN}${ADMIN_PASSWORD}${NC}"
echo ""

echo -e "${BLUE}Useful Commands:${NC}"
echo -e "  View pods:    ${YELLOW}kubectl get pods -n ${NAMESPACE}${NC}"
echo -e "  View logs:    ${YELLOW}kubectl logs -f -n ${NAMESPACE} -l app=backend${NC}"
echo -e "  View all:     ${YELLOW}kubectl get all -n ${NAMESPACE}${NC}"
echo -e "  Delete all:   ${YELLOW}kubectl delete namespace ${NAMESPACE}${NC}"
echo ""

print_success "Platform is ready! 🚀"
