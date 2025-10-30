# Quick Installation Guide

**One-command installation for MentalHealth Platform**

This guide shows you how to install the complete MentalHealth Platform on a fresh server with a single command.

---

## 🚀 Quick Start

### Local Installation (Docker)

Install everything on your local machine or server with Docker:

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-all.sh | bash
```

**That's it!** The script will:
- ✅ Install Docker & Docker Compose
- ✅ Clone the repository
- ✅ Generate secure configuration
- ✅ Build and start all services
- ✅ Run database migrations
- ✅ Create an admin user
- ✅ Show you the URLs to access the platform

**Access your platform at:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Admin Panel: http://localhost:3000/admin

---

### Kubernetes Installation

Install on a Kubernetes cluster (or create one with minikube/kind):

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-k8s-all.sh | bash
```

**The script will:**
- ✅ Install kubectl
- ✅ Set up a Kubernetes cluster (if needed)
- ✅ Clone the repository
- ✅ Deploy all components (PostgreSQL HA, Redis, Backend, Frontend)
- ✅ Configure monitoring
- ✅ Create admin user
- ✅ Show access instructions

---

## 📋 Prerequisites

### For Local Installation (Docker)
- **Operating System**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or macOS
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 20GB free space
- **Permissions**: Sudo access

### For Kubernetes Installation
- **Operating System**: Ubuntu 20.04+, Debian 11+, CentOS 8+, or macOS
- **RAM**: 8GB minimum, 16GB recommended
- **Disk Space**: 50GB free space
- **Permissions**: Sudo access
- **Kubernetes Cluster** (optional): The script can create one with minikube or kind

---

## 🔧 Supported Operating Systems

### ✅ Fully Supported
- Ubuntu 20.04 LTS / 22.04 LTS / 24.04 LTS
- Debian 11 (Bullseye) / 12 (Bookworm)
- CentOS 8 / Rocky Linux 8 / AlmaLinux 8
- Fedora 38+
- macOS 12+ (Monterey, Ventura, Sonoma)

### ⚠️ Requires Manual Docker Desktop Installation
- Windows 10/11 with WSL2 (install Docker Desktop first, then run in WSL2)

---

## 📖 Detailed Instructions

### Local Installation Step-by-Step

1. **Download and run the installation script:**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-all.sh | bash
```

2. **Follow the prompts:**
   - Press Enter to accept default admin credentials
   - Or enter custom email, username, and password

3. **Wait for installation to complete** (5-10 minutes on first run)

4. **Access the platform:**
   - Open http://localhost:3000 in your browser
   - Login with admin credentials shown at the end

5. **Start using the platform!**
   - Go to Admin Panel: http://localhost:3000/admin
   - Upload training datasets
   - Train AI models
   - Start helping users!

### Kubernetes Installation Step-by-Step

1. **Download and run the installation script:**

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/scripts/install-k8s-all.sh | bash
```

2. **Choose your cluster option:**
   - `1` - Use existing cluster (if you already have kubectl configured)
   - `2` - Install and use minikube (recommended for local testing)
   - `3` - Install and use kind (Kubernetes in Docker)

3. **Follow the prompts:**
   - Enter admin credentials or press Enter for defaults

4. **Wait for deployment** (10-15 minutes)

5. **Set up port forwarding** (if not using LoadBalancer):

```bash
# In one terminal
kubectl port-forward -n mentalhealth svc/frontend-service 3000:3000

# In another terminal
kubectl port-forward -n mentalhealth svc/backend-service 8000:8000
```

6. **Access the platform at http://localhost:3000**

---

## 🎯 What Gets Installed

### Local (Docker) Installation

**System Dependencies:**
- Docker Engine (latest)
- Docker Compose v2 (latest)
- Git
- OpenSSL
- curl, wget

**Platform Services:**
- PostgreSQL 15 (database)
- Redis 7 (cache)
- Backend API (FastAPI + Python 3.11)
- Frontend (Next.js 15 + React 19)

**Configuration:**
- Secure `.env` file with random secrets
- Database with migrations applied
- Admin user created

### Kubernetes Installation

**System Dependencies:**
- kubectl (v1.28+)
- Docker Engine (for minikube/kind)
- Git
- OpenSSL
- Optional: minikube or kind

**Platform Components:**
- PostgreSQL StatefulSet (3 replicas, HA)
- Redis Deployment (3 replicas)
- Backend Deployment with HPA (3-10 replicas)
- Frontend Deployment with HPA (3-10 replicas)
- NGINX Ingress Controller
- Network Policies
- ConfigMaps and Secrets
- Storage Classes

---

## 🔐 Security

### Automatically Generated Secrets

The installation scripts automatically generate secure random secrets:
- Database password (32 characters)
- Redis password (32 characters)
- JWT secret key (64 characters hex)
- Application secret key (64 characters hex)

### Default Admin Credentials

By default, the admin user is created with:
- **Email**: admin@mentalhealth.com
- **Username**: admin
- **Password**: admin123

**⚠️ IMPORTANT:** Change these credentials immediately after first login!

### Where Secrets are Stored

**Local Installation:**
- File: `~/MentalHealth/.env`
- Permissions: Should be readable only by you
- **Action**: `chmod 600 ~/MentalHealth/.env`

**Kubernetes Installation:**
- Kubernetes Secret: `app-secrets` in namespace `mentalhealth`
- File: `~/MentalHealth/k8s/secrets/app-secrets-generated.yaml`
- **Action**: Delete the file after deployment for security

---

## 🐛 Troubleshooting

### Local Installation Issues

**Problem: Docker permission denied**
```bash
# Solution: Add user to docker group and re-login
sudo usermod -aG docker $USER
# Then log out and back in, or run:
newgrp docker
```

**Problem: Port 3000 or 8000 already in use**
```bash
# Find what's using the port
sudo lsof -i :3000
sudo lsof -i :8000

# Kill the process or change ports in docker-compose.full.yaml
```

**Problem: Services won't start**
```bash
# Check logs
cd ~/MentalHealth
docker-compose -f docker-compose.full.yaml logs

# Restart services
docker-compose -f docker-compose.full.yaml restart
```

### Kubernetes Installation Issues

**Problem: kubectl not found after installation**
```bash
# Reload shell configuration
source ~/.bashrc
# Or
source ~/.zshrc
```

**Problem: Minikube won't start**
```bash
# Try with different driver
minikube start --driver=virtualbox
# Or
minikube start --driver=kvm2
```

**Problem: Pods not starting**
```bash
# Check pod status
kubectl get pods -n mentalhealth

# Describe pod for details
kubectl describe pod <pod-name> -n mentalhealth

# Check logs
kubectl logs <pod-name> -n mentalhealth
```

**Problem: Services not accessible**
```bash
# Verify port forwarding is running
kubectl port-forward -n mentalhealth svc/frontend-service 3000:3000

# Check service endpoints
kubectl get endpoints -n mentalhealth
```

---

## 🔄 Updating the Platform

### Update Local Installation

```bash
cd ~/MentalHealth
git pull origin main
docker-compose -f docker-compose.full.yaml down
docker-compose -f docker-compose.full.yaml build --no-cache
docker-compose -f docker-compose.full.yaml up -d
```

### Update Kubernetes Deployment

```bash
cd ~/MentalHealth
git pull origin main
kubectl apply -f k8s/app/backend-deployment.yaml
kubectl apply -f k8s/app/frontend-deployment.yaml
kubectl rollout status deployment/backend-deployment -n mentalhealth
kubectl rollout status deployment/frontend-deployment -n mentalhealth
```

---

## 🗑️ Uninstalling

### Remove Local Installation

```bash
# Stop and remove containers
cd ~/MentalHealth
docker-compose -f docker-compose.full.yaml down -v

# Remove images
docker images | grep mentalhealth | awk '{print $3}' | xargs docker rmi

# Remove installation directory
cd ~
rm -rf MentalHealth

# Optional: Uninstall Docker
# Ubuntu/Debian:
sudo apt-get remove docker-ce docker-ce-cli containerd.io
# CentOS/RHEL:
sudo yum remove docker-ce docker-ce-cli containerd.io
```

### Remove Kubernetes Deployment

```bash
# Delete namespace (removes everything)
kubectl delete namespace mentalhealth

# If using minikube
minikube stop
minikube delete

# If using kind
kind delete cluster

# Remove installation directory
rm -rf ~/MentalHealth
```

---

## 📊 Resource Requirements

### Local Installation

| Component | CPU | Memory | Disk |
|-----------|-----|--------|------|
| PostgreSQL | 0.5 CPU | 512 MB | 10 GB |
| Redis | 0.25 CPU | 256 MB | 1 GB |
| Backend | 1 CPU | 1 GB | 2 GB |
| Frontend | 0.5 CPU | 512 MB | 1 GB |
| **Total** | **2.25 CPU** | **2.25 GB** | **14 GB** |

### Kubernetes Installation

| Component | Min Resources | Recommended |
|-----------|---------------|-------------|
| Control Plane | 2 CPU, 4 GB RAM | 4 CPU, 8 GB RAM |
| Worker Nodes | 4 CPU, 8 GB RAM | 8 CPU, 16 GB RAM |
| Storage | 50 GB | 100 GB |

---

## 🎓 Next Steps

After installation:

1. **Login to the platform**
   - Open http://localhost:3000
   - Use admin credentials

2. **Change admin password**
   - Go to Profile Settings
   - Update password immediately

3. **Access Admin Panel**
   - Go to http://localhost:3000/admin
   - This is where you manage the platform

4. **Upload Training Datasets**
   - Admin Panel → Datasets → Upload
   - Support formats: JSON, CSV

5. **Train AI Models**
   - Admin Panel → Training → Start New Training
   - Train all 4 models:
     - Emotion Classifier
     - Mood Predictor
     - Chat Generator
     - Sentiment Analyzer

6. **Activate Models**
   - Admin Panel → Models → Activate
   - Activate your trained models

7. **Create Test Users**
   - Create therapist and patient accounts
   - Test the platform features

8. **Configure Monitoring** (Kubernetes only)
   ```bash
   ./scripts/setup-monitoring.sh
   ```

---

## 📚 Additional Documentation

For more detailed information, see:

- [Complete Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Deployment Scripts Documentation](./DEPLOYMENT_SCRIPTS.md)
- [Complete System Overview](./COMPLETE_SYSTEM_OVERVIEW.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [Main README](../README.md)

---

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs:
   - Local: `docker-compose -f docker-compose.full.yaml logs`
   - K8s: `kubectl logs -n mentalhealth -l app=backend`
3. Check GitHub Issues: https://github.com/TheRealHZL/MentalHealth/issues
4. Create a new issue with:
   - Your OS and version
   - Installation method used
   - Complete error message
   - Relevant logs

---

## 🌟 Features Installed

After successful installation, you'll have:

- ✅ Complete mental health platform
- ✅ User authentication and authorization
- ✅ Therapist and patient dashboards
- ✅ AI-powered chat therapy (4 custom PyTorch models)
- ✅ Mood tracking and analysis
- ✅ Dream journal with AI insights
- ✅ Thought recording with sentiment analysis
- ✅ Feedback system
- ✅ Analytics and reporting
- ✅ Admin panel for platform management
- ✅ Training pipeline for AI models
- ✅ Dataset management
- ✅ Model versioning and activation
- ✅ User management
- ✅ High availability (Kubernetes)
- ✅ Auto-scaling (Kubernetes)
- ✅ Production-ready security

---

## 📝 Installation Summary

| Method | Time | Difficulty | Use Case |
|--------|------|------------|----------|
| Local (Docker) | 5-10 min | Easy | Development, Testing, Small deployments |
| Kubernetes | 10-15 min | Medium | Production, Scalable deployments |

**Choose Local if:**
- You want quick testing
- You're developing
- You have limited resources
- You want simplicity

**Choose Kubernetes if:**
- You need high availability
- You expect high traffic
- You want auto-scaling
- You need production features

---

**Last Updated**: 2025-10-30

**Script Versions**:
- install-all.sh: v1.0.0
- install-k8s-all.sh: v1.0.0

**Maintained By**: MentalHealth Platform Team
