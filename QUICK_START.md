# 🚀 Quick Start Guide - MentalHealth Platform

Get up and running in **5 minutes**!

## Prerequisites

- Docker Desktop installed
- 8GB RAM available
- 20GB disk space
- Terminal/Command Line

## 1. Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/YourOrg/MentalHealth.git
cd MentalHealth

# Copy environment file
cp .env.example .env

# Edit .env - Add your OpenAI API key (required)
nano .env  # or use your favorite editor
# Set: OPENAI_API_KEY=sk-your-actual-key-here
```

## 2. Start Everything (2 minutes)

```bash
# Start all services
docker-compose -f docker-compose.full.yaml up -d

# Wait for services to be healthy (1-2 minutes)
# Watch the startup
docker-compose -f docker-compose.full.yaml logs -f
```

When you see "Application startup complete", proceed!

## 3. Initialize Database (1 minute)

```bash
# Run database migrations
docker-compose -f docker-compose.full.yaml exec backend alembic upgrade head

# (Optional) Load test data
docker-compose -f docker-compose.full.yaml exec backend python scripts/seed_data.py
```

## 4. Access Applications

🌐 **Frontend**: http://localhost:3000
🔌 **Backend API**: http://localhost:8000
📚 **API Documentation**: http://localhost:8000/docs
🗄️ **Database Admin**: http://localhost:5050 (start with `--profile tools`)

## 5. Test It Works

### Via Browser

1. Open http://localhost:3000
2. Create an account
3. Start a chat session

### Via API

```bash
# Health check
curl http://localhost:8000/health

# Get API info
curl http://localhost:8000/api/v1/info
```

## Stop Services

```bash
# Stop (keeps data)
docker-compose -f docker-compose.full.yaml down

# Stop and remove all data
docker-compose -f docker-compose.full.yaml down -v
```

## Common Issues

### Port already in use

```bash
# Check what's using the port
lsof -i :8000  # Backend
lsof -i :3000  # Frontend

# Kill the process or change ports in docker-compose.full.yaml
```

### Services won't start

```bash
# Check logs
docker-compose -f docker-compose.full.yaml logs backend
docker-compose -f docker-compose.full.yaml logs frontend

# Restart specific service
docker-compose -f docker-compose.full.yaml restart backend
```

### Database connection error

```bash
# Make sure PostgreSQL is healthy
docker-compose -f docker-compose.full.yaml ps postgres

# Should show "healthy" status
```

## Next Steps

- 📖 Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production deployment
- 🔒 Review [Security Configuration](SECURITY_AUDIT_PHASE3.md)
- ☸️ Deploy to [Kubernetes](k8s/README.md)
- 🔄 Set up [CI/CD Pipeline](.github/workflows/ci-cd.yaml)

## Development Mode

Want to develop with live reload?

```bash
# Backend only (develop in src/)
docker-compose up -d postgres redis
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Frontend only (develop in frontend/)
cd frontend
npm install
npm run dev
```

## Need Help?

- 📚 Full documentation: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 🐛 Issues: [GitHub Issues](https://github.com/YourOrg/MentalHealth/issues)
- 💬 Slack: #mentalhealth-dev

---

**That's it!** You're now running the full MentalHealth platform locally. 🎉
