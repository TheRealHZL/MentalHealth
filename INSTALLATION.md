# MindBridge AI Platform - Installation Guide

## 🚀 Quick Installation (Recommended)

### One-Line Install

The easiest way to get started:

```bash
curl -fsSL https://raw.githubusercontent.com/TheRealHZL/MentalHealth/main/quickstart.sh | bash
```

This interactive script will:
- Ask you to choose deployment mode (Docker/Local/Kubernetes)
- Optionally configure domain and SSL
- Automatically install everything
- Start the application

**Installation time:** 5-15 minutes

---

## 📦 Installation Methods

### Method 1: Docker (Recommended)

**Best for:** Quick start, development, single-server production

```bash
# Clone repository
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth

# Run installer
chmod +x install.sh
./install.sh --mode docker
```

**What gets installed:**
- Docker and Docker Compose
- PostgreSQL database (in container)
- Redis cache (in container)
- Backend API (in container)
- Frontend (in container)
- AI models (trained automatically)

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Method 2: Local Installation

**Best for:** Development, customization

```bash
# Clone repository
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth

# Run installer
chmod +x install.sh
./install.sh --mode local
```

**What gets installed:**
- Python 3.11+ and dependencies
- Node.js 18+ and npm
- PostgreSQL 15+ (system)
- Redis 7+ (system)
- Nginx (optional, for SSL)
- AI models (trained locally)

**Requirements:**
- Ubuntu 20.04+, Debian 11+, CentOS 8+, or macOS
- 4GB RAM minimum
- 10GB disk space

---

### Method 3: Kubernetes

**Best for:** Production, high availability, scalability

```bash
# Clone repository
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth

# Run installer
chmod +x install.sh
./install.sh --mode kubernetes
```

**Prerequisites:**
- Kubernetes cluster (1.24+)
- kubectl configured
- At least 3 nodes recommended

**What gets deployed:**
- PostgreSQL StatefulSet (HA)
- Redis Deployment
- Backend Deployment (3 replicas)
- Frontend Deployment (3 replicas)
- Ingress Controller
- Persistent Volumes

---

## 🔧 Advanced Installation Options

### Production with SSL

```bash
./install.sh --mode docker --domain yourdomain.com --email admin@yourdomain.com
```

This will:
- Install and configure the application
- Set up Nginx reverse proxy
- Obtain Let's Encrypt SSL certificate
- Configure auto-renewal

### Custom Installation Directory

```bash
INSTALL_DIR=/custom/path ./install.sh --mode docker
```

### Skip AI Model Training

If you want to train models later or use pre-trained models:

```bash
./install.sh --mode docker --no-models
```

You can train models later with:

```bash
docker-compose exec backend python -m src.ai.training.trainer --all
```

### Skip Dependency Installation

If you already have Docker/dependencies installed:

```bash
./install.sh --mode docker --skip-deps
```

---

## 🔄 Updating

### Automatic Update

```bash
cd /opt/mindbridge  # or your installation directory
./update.sh
```

### Update Options

```bash
# Check for updates without applying
./update.sh --check

# Force update even if up to date
./update.sh --force

# Update without restarting services
./update.sh --no-restart

# Create backup before updating
./update.sh --backup
```

### Manual Update

**Docker:**
```bash
cd /opt/mindbridge
git pull origin main
docker-compose down
docker-compose up -d --build
docker-compose exec backend alembic upgrade head
```

**Local:**
```bash
cd /opt/mindbridge
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
alembic upgrade head
sudo systemctl restart mindbridge-backend mindbridge-frontend
```

**Kubernetes:**
```bash
cd /opt/mindbridge
git pull origin main
kubectl apply -f k8s/
kubectl rollout restart deployment -n mindbridge
```

---

## 🛠 Manual Installation (Advanced)

If you prefer manual control:

### 1. Clone Repository

```bash
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth
```

### 2. Configure Environment

```bash
cp .env.example .env
nano .env  # Edit configuration
```

Generate secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Database Setup

```bash
# Create database
sudo -u postgres createdb mindbridge_db
sudo -u postgres createuser mindbridge_user -P

# Grant permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mindbridge_db TO mindbridge_user;"
```

### 4. Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Train AI models
python -m src.ai.training.data.sample_data_generator
python -m src.ai.training.trainer --all

# Start backend
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Start frontend
npm start
```

---

## 📋 System Requirements

### Minimum Requirements

- **CPU:** 2 cores
- **RAM:** 4GB
- **Disk:** 10GB free space
- **OS:** Ubuntu 20.04+, Debian 11+, CentOS 8+, macOS 11+

### Recommended for Production

- **CPU:** 4+ cores
- **RAM:** 8GB+
- **Disk:** 50GB+ SSD
- **OS:** Ubuntu 22.04 LTS
- **Network:** 100 Mbps+

### For AI Model Training

- **CPU:** 4+ cores (8+ recommended)
- **RAM:** 8GB+ (16GB recommended)
- **GPU:** Optional (CUDA-compatible, significantly faster)

---

## 🐳 Docker Installation

### Using Docker Compose

```bash
# Clone repository
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth

# Copy environment file
cp .env.example .env
nano .env  # Configure

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose Files

- `docker-compose.yml` - Development
- `docker-compose.prod.yml` - Production

### Using Pre-built Images

```bash
docker pull ghcr.io/yourusername/mindbridge-backend:latest
docker pull ghcr.io/yourusername/mindbridge-frontend:latest
```

---

## ☸️ Kubernetes Installation

### Prerequisites

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify
kubectl version --client
```

### Deploy to Kubernetes

```bash
# Clone repository
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth/k8s

# Create namespace
kubectl create namespace mindbridge

# Create secrets
kubectl create secret generic mindbridge-secrets \
  --from-literal=secret-key="your-secret-key" \
  --from-literal=db-password="your-db-password" \
  -n mindbridge

# Deploy
kubectl apply -f namespace.yaml
kubectl apply -f configmaps/
kubectl apply -f postgres/
kubectl apply -f redis/
kubectl apply -f backend/
kubectl apply -f frontend/
kubectl apply -f ingress/

# Check status
kubectl get pods -n mindbridge
kubectl logs -n mindbridge -l app=backend
```

---

## 🔐 Security Setup

### 1. Generate Strong Secrets

```bash
# Secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Database password
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

### 2. Configure Firewall

```bash
# Allow SSH, HTTP, HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. SSL Certificate

**Automatic (with installer):**
```bash
./install.sh --mode docker --domain yourdomain.com --email admin@yourdomain.com
```

**Manual:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 🧪 Development Setup

### Quick Dev Environment

```bash
# Clone repo
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth

# Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Hot Reload

Both backend and frontend support hot reload during development:

- **Backend:** Changes to Python files automatically reload
- **Frontend:** Changes to React components automatically reload

---

## 📊 Monitoring Setup

### Install Prometheus + Grafana

```bash
cd MentalHealth
./scripts/setup-monitoring.sh
```

**Access:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### Pre-configured Dashboards

- API Metrics
- Database Performance
- AI Model Usage
- System Resources

---

## 🆘 Troubleshooting

### Installation Failed

**Check logs:**
```bash
# Docker
docker-compose logs

# Local
sudo journalctl -u mindbridge-backend -f

# Kubernetes
kubectl logs -n mindbridge -l app=backend
```

### Database Connection Failed

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -h localhost -U mindbridge_user -d mindbridge_db
```

### Port Already in Use

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### AI Models Not Loading

```bash
# Re-train models
docker-compose exec backend python -m src.ai.training.trainer --all

# Check model files exist
ls -lh data/models/
```

### Permission Denied

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/mindbridge

# Fix permissions
chmod +x install.sh update.sh
```

---

## 📚 Next Steps

After installation:

1. **Access the Application**
   - Open http://localhost:3000 in your browser
   - Register as a patient (no verification needed)

2. **Explore Features**
   - Create your first mood entry
   - Log a dream
   - Try AI-powered insights

3. **Admin Access** (optional)
   - Create admin user via backend
   - Access training interface at /admin

4. **Production Deployment**
   - Review [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md)
   - Set up monitoring
   - Configure backups

---

## 🔗 Additional Resources

- [API Documentation](./API.md)
- [Production Deployment Guide](./PRODUCTION_DEPLOYMENT.md)
- [Kubernetes Guide](./KUBERNETES.md)
- [Monitoring Setup](./MONITORING.md)
- [Contributing Guide](../CONTRIBUTING.md)

---

## 💬 Support

- **Issues:** https://github.com/TheRealHZL/MentalHealth/issues
- **Email:** support@mindbridge.app
- **Security:** security@mindbridge.app

---

## 📝 License

Copyright © 2025 MindBridge AI Platform
