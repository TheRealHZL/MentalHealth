# 🧠 MindBridge AI Platform

**Enterprise-Ready Mental Health Platform with Modular Architecture**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()

> **AI-powered mental health platform with privacy-first design and modular plug-and-play architecture**

---

## 🚀 What's New in v2.0

### ⭐ Enterprise-Ready Architecture

- **🔌 Modular System**: Plug-and-play modules in `/app/modules/`
- **📦 Auto-Discovery**: Modules automatically loaded at startup
- **🎯 Easy Extension**: Add features without touching core code
- **🧪 Testable**: Isolated, independently testable modules
- **📊 Maintainable**: Clear separation of concerns

### 🏗️ New Project Structure

```
mindbridge/
├── app/                      # Application code
│   ├── core/                 # Core functionality
│   │   ├── config.py         # Settings & configuration
│   │   ├── database.py       # Database connection
│   │   ├── module_loader.py  # Module auto-loader ⭐
│   │   ├── security.py       # Authentication & security
│   │   └── utils.py          # Utilities
│   ├── modules/              # Feature modules
│   │   ├── mood/             # Mood tracking
│   │   ├── dreams/           # Dream journal
│   │   ├── therapy/          # Therapy tools
│   │   ├── admin/            # Admin dashboard
│   │   ├── ai_training/      # In-house AI training
│   │   ├── analytics/        # Analytics & insights
│   │   └── users/            # User management
│   └── main.py               # Application entry point
├── scripts/                  # Utility scripts
│   ├── install.sh            # Robust installation ⭐
│   ├── update.sh             # Safe updates with rollback ⭐
│   └── start.sh              # Start services
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── e2e/                  # End-to-end tests
├── docs/                     # Documentation
│   ├── MODULE_GUIDE.md       # How to create modules ⭐
│   └── API_DOCS.md           # API documentation
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies ⭐
└── pyproject.toml            # Code quality config ⭐
```

---

## ✨ Features

### 🎯 Core Features

- **📊 Mood Tracking**: Comprehensive mood logging with AI insights
- **💭 Dream Journal**: Record and analyze dreams
- **📝 Therapy Tools**: CBT/DBT worksheets and self-reflection
- **📈 Analytics**: Pattern recognition and trend analysis
- **🤝 Secure Sharing**: GDPR-compliant data sharing with therapists
- **🤖 In-House AI**: PyTorch-based models (no external APIs)

### 🔐 Security & Privacy

- **🛡️ Patient Control**: You own your data
- **🔒 End-to-End Encryption**: Client-side encryption option
- **🍪 httpOnly Cookies**: XSS-protected authentication
- **⚡ Rate Limiting**: Protection against abuse
- **📋 GDPR Compliant**: Full data export & deletion
- **🔑 Row-Level Security**: Database-level isolation

### 🚀 Enterprise Features

- **📦 Modular Architecture**: Easy to extend
- **🔌 Plugin System**: Add features without core changes
- **🧪 Comprehensive Tests**: Unit, integration, E2E
- **📊 Monitoring**: Prometheus metrics & health checks
- **🐳 Docker Support**: Production-ready containers
- **☸️ Kubernetes Ready**: K8s manifests included

---

## 📦 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL 14+
- Node.js 18+ (for frontend)

### Installation

```bash
# Clone repository
git clone https://github.com/TheRealHZL/MentalHealth.git
cd MentalHealth

# Run installation script
./scripts/install.sh

# For development mode (includes dev tools)
./scripts/install.sh --dev
```

The installation script will:
- ✅ Check system requirements
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Set up database
- ✅ Run migrations
- ✅ Validate modules
- ✅ Configure code quality tools (dev mode)

### Configuration

```bash
# Edit environment variables
cp .env.example .env
vim .env

# Key settings:
# - SECRET_KEY: Auto-generated secure key
# - DATABASE_URL: PostgreSQL connection
# - AI_ENGINE_ENABLED: Enable in-house AI (true/false)
# - ENVIRONMENT: development/production
```

### Start Services

```bash
# Start all services (database, backend, frontend)
docker-compose up -d

# Or start individually
docker-compose up -d db        # Database only
docker-compose up -d backend   # Backend API
docker-compose up -d frontend  # Next.js frontend

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### Access the Platform

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs
- **Admin Panel**: http://localhost:3000/admin
- **Health Check**: http://localhost:8080/health

---

## 🔧 Development

### Setup Development Environment

```bash
# Install with development tools
./scripts/install.sh --dev

# Activate virtual environment
source venv/bin/activate

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Lint
flake8 app/
pylint app/

# Type checking
mypy app/

# Security scan
bandit -r app/

# Run all checks
./scripts/quality_check.sh
```

### Creating a New Module

See [`docs/MODULE_GUIDE.md`](docs/MODULE_GUIDE.md) for detailed instructions.

**Quick example**:

```bash
# 1. Create module directory
mkdir -p app/modules/my_module

# 2. Create manifest.json
cat > app/modules/my_module/manifest.json << EOF
{
  "name": "my_module",
  "version": "1.0.0",
  "description": "My awesome module",
  "enabled": true,
  "routes_prefix": "/api/v1/my-module",
  "tags": ["my-module"],
  "dependencies": [],
  "author": "Your Name"
}
EOF

# 3. Create routes.py
cat > app/modules/my_module/routes.py << EOF
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_items():
    return {"message": "Hello from my_module"}
EOF

# 4. Create __init__.py
touch app/modules/my_module/__init__.py

# 5. Restart and test
docker-compose restart backend
curl http://localhost:8080/api/v1/my-module/
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=app --cov-report=html

# Specific module
pytest tests/unit/test_mood.py -v
```

### Test Structure

```
tests/
├── unit/                 # Fast, isolated unit tests
│   ├── test_mood.py
│   ├── test_dreams.py
│   └── test_security.py
├── integration/          # Tests with database/services
│   ├── test_api.py
│   └── test_module_loader.py
└── e2e/                  # End-to-end user flows
    ├── test_user_journey.py
    └── test_mood_tracking_flow.py
```

---

## 📊 Module System

### How It Works

1. **Discovery**: Module loader scans `/app/modules/` at startup
2. **Validation**: Checks `manifest.json` and dependencies
3. **Loading**: Imports `routes.py` and extracts router
4. **Registration**: Registers with FastAPI automatically

### Available Modules

| Module | Description | Status |
|--------|-------------|--------|
| `mood` | Mood tracking & analysis | ✅ Active |
| `dreams` | Dream journal & interpretation | ✅ Active |
| `therapy` | Therapy worksheets & tools | ✅ Active |
| `admin` | Admin dashboard & management | ✅ Active |
| `ai_training` | In-house AI model training | ✅ Active |
| `analytics` | Advanced analytics & insights | ✅ Active |
| `sharing` | Secure data sharing | ✅ Active |
| `users` | Authentication & profiles | ✅ Active |

### Check Loaded Modules

```bash
# Via API
curl http://localhost:8080/api/v1/modules | jq

# Via logs
docker-compose logs backend | grep "Loaded module"
```

---

## 🔄 Updates

### Safe Update Process

```bash
# Run update script (includes backup & rollback)
./scripts/update.sh

# Skip backup (if you have external backups)
./scripts/update.sh --skip-backup

# Skip migrations (if no DB changes)
./scripts/update.sh --skip-migrations
```

The update script will:
- ✅ Create backup (database, .env, uploads)
- ✅ Pull latest code
- ✅ Update dependencies
- ✅ Run migrations
- ✅ Validate modules
- ✅ Restart services
- ✅ Run health checks

### Rollback if Needed

```bash
# Rollback database
psql < backups/20241101_120000/database.sql

# Rollback code
git reset --hard HEAD~1

# Restart services
docker-compose restart
```

---

## 🐳 Docker Deployment

### Production Deployment

```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale backend
docker-compose up -d --scale backend=3
```

### Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n mindbridge

# View logs
kubectl logs -f -n mindbridge -l app=backend
```

---

## 📚 Documentation

- **[Module Guide](docs/MODULE_GUIDE.md)**: How to create modules
- **[API Documentation](docs/API_DOCS.md)**: API endpoints reference
- **[Installation Guide](docs/INSTALLATION.md)**: Detailed setup instructions
- **[Security Guide](docs/SECURITY_AUDIT_PHASE3.md)**: Security features
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)**: Production deployment

---

## 🏛️ Architecture

### High-Level Overview

```
┌─────────────┐
│   Frontend  │  Next.js 14 + TypeScript
│  (Port 3000)│
└──────┬──────┘
       │
       │ HTTP/REST
       │
┌──────▼──────┐
│   Backend   │  FastAPI + Python 3.10
│  (Port 8080)│  Module Loader ⭐
└──────┬──────┘
       │
       ├──────────┬────────────┬──────────┐
       │          │            │          │
┌──────▼──┐  ┌───▼────┐  ┌────▼────┐  ┌─▼─────┐
│PostgreSQL│  │ Redis  │  │AI Engine│  │Modules│
│  (5432)  │  │ (6379) │  │(PyTorch)│  │       │
└──────────┘  └────────┘  └─────────┘  └───────┘
```

### Module Architecture

```
┌────────────────────────────────────┐
│         FastAPI Application        │
│                                    │
│  ┌──────────────────────────────┐ │
│  │      Module Loader ⭐        │ │
│  │  - Auto-discover modules     │ │
│  │  - Validate manifests        │ │
│  │  - Load routers              │ │
│  │  - Register with FastAPI     │ │
│  └──────────────────────────────┘ │
│                                    │
│  ┌─────┐ ┌──────┐ ┌───────┐      │
│  │Mood │ │Dreams│ │Therapy│ ...  │
│  └─────┘ └──────┘ └───────┘      │
└────────────────────────────────────┘
```

---

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Write** code and tests
4. **Run** tests and quality checks
5. **Commit**: `git commit -m "Add my feature"`
6. **Push**: `git push origin feature/my-feature`
7. **Create** Pull Request

### Code Standards

- **Python**: PEP 8, Black formatting, type hints
- **Tests**: Minimum 80% coverage
- **Documentation**: Docstrings for all public functions
- **Commits**: Conventional commits format

---

## 📄 License

Proprietary - © 2024 MindBridge Team

---

## 🆘 Support

- **Documentation**: `/docs/`
- **Issues**: [GitHub Issues](https://github.com/TheRealHZL/MentalHealth/issues)
- **Email**: support@mindbridge.app

---

## 🙏 Acknowledgments

- **FastAPI**: Modern Python web framework
- **PyTorch**: In-house AI models
- **PostgreSQL**: Reliable database
- **Next.js**: React framework for frontend
- **Community**: All contributors and supporters

---

**Built with ❤️ for mental health and privacy**
