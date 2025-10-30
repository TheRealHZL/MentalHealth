# 🧠 MentalHealth Platform

> **Enterprise-grade mental health support platform with AI-powered therapy, secure data handling, and production-ready infrastructure**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-ready-blue.svg)](https://kubernetes.io/)
[![Docker](https://img.shields.io/badge/Docker-ready-blue.svg)](https://www.docker.com/)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [Security](#-security)
- [Contributing](#-contributing)

---

## 🎯 Overview

MentalHealth is a comprehensive, production-ready platform designed to provide mental health support through AI-powered conversations, mood tracking, and therapeutic interventions. Built with modern technologies and enterprise-grade infrastructure, it's ready to scale from local development to production deployment on Kubernetes.

### Key Highlights

- 🤖 **AI-Powered Therapy** - Intelligent chat-based mental health support
- 🔒 **Enterprise Security** - OWASP hardened with multiple security layers
- 📊 **Complete Monitoring** - Prometheus, Grafana, and Alertmanager integration
- 🚀 **Auto-Scaling** - Kubernetes-ready with HPA configuration
- 🐳 **Docker Ready** - Complete containerization for all services
- 🔄 **CI/CD Pipeline** - Automated testing, building, and deployment
- 📚 **Comprehensive Docs** - Complete guides for deployment and development

---

## ✨ Features

### Core Functionality

- **AI Chat Therapy** - Real-time therapeutic conversations powered by custom PyTorch AI models
- **User Authentication** - JWT-based secure authentication with session management
- **Mood Tracking** - Track and analyze emotional patterns over time
- **Secure Data Storage** - Encrypted data at rest and in transit
- **Rate Limiting** - Built-in protection against abuse (100 req/min)
- **Real-time Metrics** - Monitor application performance and health

### Technical Features

- **High Availability** - PostgreSQL StatefulSet with 3 replicas
- **Caching Layer** - Redis cluster for session management and caching
- **Load Balancing** - NGINX Ingress with security features
- **Auto-Scaling** - Horizontal Pod Autoscaler (HPA) configured
- **Security Hardening** - XSS, CSRF, SQL Injection protection
- **Monitoring Stack** - Prometheus, Grafana, Alertmanager
- **CI/CD** - GitHub Actions for automated workflows

---

## 🚀 Quick Start

### Prerequisites

- Docker Desktop 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 20GB free disk space

### Local Development (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/YourOrg/MentalHealth.git
cd MentalHealth

# 2. Set up environment
cp .env.example .env
# No API keys needed! All AI runs locally with custom models

# 3. Start all services
docker-compose -f docker-compose.full.yaml up -d

# 4. Initialize database
docker-compose -f docker-compose.full.yaml exec backend alembic upgrade head

# 5. Access applications
# Frontend:  http://localhost:3000
# Backend:   http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

### Stop Services

```bash
# Stop containers (keeps data)
docker-compose -f docker-compose.full.yaml down

# Stop and remove all data
docker-compose -f docker-compose.full.yaml down -v
```

> 📖 **Need more details?** See [QUICK_START.md](QUICK_START.md)

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / Users                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         NGINX Ingress Controller (HA, 3 replicas)           │
│  - TLS/SSL Termination                                      │
│  - Rate Limiting                                            │
│  - ModSecurity + OWASP CRS                                  │
└────────┬──────────────────────────┬─────────────────────────┘
         │                          │
         ▼                          ▼
┌──────────────────┐      ┌─────────────────────┐
│  Frontend (3)    │      │  Backend API (3)    │
│  Next.js 15      │      │  FastAPI + Python   │
│  React 19        │      │  Auto-scaling       │
└──────────────────┘      └────┬────────┬───────┘
                               │        │
                 ┌─────────────┘        └────────────┐
                 ▼                                    ▼
┌─────────────────────────┐        ┌──────────────────────────┐
│ PostgreSQL (3 replicas) │        │  Redis Cache (3 replicas)│
│ StatefulSet with HA     │        │  Session Management      │
└─────────────────────────┘        └──────────────────────────┘
                 │                                    │
                 └──────────────┬─────────────────────┘
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Stack                          │
│  Prometheus (2) | Grafana (2) | Alertmanager (2)           │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

| Component | Technology | Replicas | Purpose |
|-----------|-----------|----------|---------|
| **Frontend** | Next.js 15, React 19 | 3+ (HPA) | User interface |
| **Backend** | FastAPI, Python 3.11 | 3+ (HPA) | API and business logic |
| **Database** | PostgreSQL 15 | 3 (HA) | Data persistence |
| **Cache** | Redis 7 | 3 | Session & caching |
| **Ingress** | NGINX | 3 | Load balancing & TLS |
| **Monitoring** | Prometheus/Grafana | 2 | Metrics & dashboards |

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **PyTorch** - Machine learning models
- **Pydantic** - Data validation
- **Redis** - Caching and sessions

### Frontend
- **Next.js 15** - React framework with App Router
- **React 19** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS
- **Zustand** - State management

### Infrastructure
- **Kubernetes** - Container orchestration
- **Docker** - Containerization
- **PostgreSQL** - Primary database
- **Redis** - Cache and session store
- **NGINX** - Reverse proxy and ingress
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization

### DevOps
- **GitHub Actions** - CI/CD pipeline
- **Docker Compose** - Local development
- **Helm** - Kubernetes package manager (optional)
- **Kustomize** - Kubernetes configuration management

---

## 🚢 Deployment

### Docker Compose (Local/Development)

```bash
# Start full stack
docker-compose -f docker-compose.full.yaml up -d

# With monitoring
docker-compose -f docker-compose.full.yaml --profile monitoring up -d

# With development tools
docker-compose -f docker-compose.full.yaml --profile tools up -d
```

### Kubernetes (Production)

```bash
# Automated deployment
cd k8s
./deploy.sh

# Or manual deployment
kubectl apply -k k8s/

# Check status
kubectl get pods -n mentalhealth
```

### CI/CD Pipeline

The platform includes automated workflows for:
- ✅ Testing (Backend + Frontend)
- ✅ Building Docker images
- ✅ Security scanning
- ✅ Deploying to Kubernetes
- ✅ Daily security audits

> 📖 **Deployment Details**: See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 📚 Documentation

### Guides

| Document | Description |
|----------|-------------|
| [QUICK_START.md](QUICK_START.md) | Get started in 5 minutes |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Complete deployment guide |
| [TESTING_GUIDE.md](TESTING_GUIDE.md) | Testing documentation |
| [COMPLETE_SYSTEM_OVERVIEW.md](COMPLETE_SYSTEM_OVERVIEW.md) | System architecture |
| [k8s/README.md](k8s/README.md) | Kubernetes setup details |
| [SECURITY_AUDIT_PHASE3.md](SECURITY_AUDIT_PHASE3.md) | Security audit report |

### API Documentation

- **Swagger UI**: http://localhost:8000/docs (when running)
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🔐 Security

### Implemented Security Measures

- ✅ **Authentication** - JWT-based with secure session management
- ✅ **Encryption** - Data encrypted at rest and in transit
- ✅ **Rate Limiting** - Protection against brute force attacks
- ✅ **XSS Protection** - Input sanitization and output encoding
- ✅ **CSRF Protection** - Token-based CSRF protection
- ✅ **SQL Injection Prevention** - Parameterized queries
- ✅ **Security Headers** - HSTS, CSP, X-Frame-Options, etc.
- ✅ **Network Policies** - Kubernetes network isolation
- ✅ **Container Security** - Non-root users, read-only filesystems
- ✅ **Secrets Management** - Kubernetes secrets integration

### Security Scanning

- **Daily scans** with Trivy, Semgrep, Bandit, and Gitleaks
- **OWASP Top 10** compliance
- **Dependency vulnerability scanning**
- **Container image scanning**

> 📖 **Security Details**: See [SECURITY_AUDIT_PHASE3.md](SECURITY_AUDIT_PHASE3.md)

---

## 📊 Monitoring & Observability

### Available Dashboards

**Grafana** (http://localhost:3001 when running with monitoring profile):
- Kubernetes cluster overview
- PostgreSQL performance metrics
- Redis metrics
- Application performance
- API response times

**Prometheus** (http://localhost:9090):
- Custom metrics and queries
- Alert rules
- Target health status

### Key Metrics

- API response time (p50, p95, p99)
- Database connection pool usage
- Redis memory usage
- Pod CPU and memory usage
- Request rate and error rate
- Active user sessions

---

## 🧪 Testing

### Run Tests

```bash
# All tests
docker-compose -f docker-compose.full.yaml exec backend pytest

# With coverage
docker-compose -f docker-compose.full.yaml exec backend pytest --cov=src

# Specific test file
pytest tests/test_auth.py -v
```

### Test Coverage

- ✅ Unit tests
- ✅ Integration tests
- ✅ API endpoint tests
- ✅ Security tests
- ✅ Performance tests

> 📖 **Testing Details**: See [TESTING_GUIDE.md](TESTING_GUIDE.md)

---

## 🎯 Roadmap

### Phase 1: Core Features ✅
- [x] User authentication and authorization
- [x] AI chat functionality
- [x] Mood tracking
- [x] Data encryption
- [x] Rate limiting

### Phase 2: Infrastructure ✅
- [x] Docker containerization
- [x] Kubernetes manifests
- [x] High availability setup
- [x] Monitoring stack
- [x] CI/CD pipeline

### Phase 3: Production Ready ✅
- [x] Security hardening
- [x] Auto-scaling configuration
- [x] Complete documentation
- [x] Testing suite
- [x] Deployment automation

### Phase 4: Future Enhancements 🚧
- [ ] Mobile app (iOS/Android)
- [ ] Video consultations
- [ ] Advanced analytics
- [ ] Multi-language support
- [ ] GitOps with ArgoCD
- [ ] Service mesh (Istio)

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Authors

- **Your Team** - Initial work

---

## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- Next.js team for the incredible React framework
- The Kubernetes community
- All contributors and supporters

---

## 📞 Support

- **Documentation**: Check our [complete guides](DEPLOYMENT_GUIDE.md)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/YourOrg/MentalHealth/issues)
- **Discussions**: Join our community discussions

---

## 📈 Project Status

```
✅ Backend:       Production Ready
✅ Frontend:      Production Ready
✅ Infrastructure: Production Ready
✅ CI/CD:         Production Ready
✅ Documentation: Complete
✅ Security:      Hardened
✅ Monitoring:    Configured
✅ Testing:       Comprehensive

🎉 SYSTEM IS 100% READY FOR PRODUCTION 🎉
```

---

## 🌟 Star History

If you find this project helpful, please consider giving it a star ⭐

---

**Built with ❤️ for mental health support**

---

## Quick Links

- [Get Started in 5 Minutes](QUICK_START.md)
- [Deploy to Production](DEPLOYMENT_GUIDE.md)
- [Run Tests](TESTING_GUIDE.md)
- [View Architecture](COMPLETE_SYSTEM_OVERVIEW.md)
- [API Documentation](http://localhost:8000/docs)

---

*Last Updated: 2025-10-30 | Version: 1.0.0*
