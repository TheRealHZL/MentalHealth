# 🐳 Docker Setup Guide

## Quick Start

### 1. **Build & Start** (Erstmaliges Setup)

```bash
# Build containers
./docker.sh build

# Start all services
./docker.sh start

# Setup database
./docker.sh db-setup
```

### 2. **Access the API**

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **pgAdmin** (optional): http://localhost:5050

### 3. **Test the API**

```bash
# Health check
curl http://localhost:8000/ping

# Root endpoint
curl http://localhost:8000/
```

---

## 📋 Docker Commands

### Basic Operations

```bash
# Start services
./docker.sh start

# Stop services
./docker.sh stop

# Restart services
./docker.sh restart

# View logs (all services)
./docker.sh logs

# View logs (specific service)
./docker.sh logs api
./docker.sh logs postgres

# Check status
./docker.sh status
```

### Database Operations

```bash
# Run migrations
./docker.sh db-migrate

# Open database shell
./docker.sh db-shell

# Inside db-shell:
\dt                    # List tables
\d users              # Describe users table
SELECT * FROM users;  # Query users
\q                    # Quit
```

### Advanced Operations

```bash
# Execute command in API container
./docker.sh exec python --version
./docker.sh exec alembic current

# Clean up everything
./docker.sh clean
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           Docker Compose Stack              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐       │
│  │              │  │              │       │
│  │  MindBridge  │  │  PostgreSQL  │       │
│  │     API      │──│   Database   │       │
│  │  (Port 8000) │  │  (Port 5432) │       │
│  │              │  │              │       │
│  └──────┬───────┘  └──────────────┘       │
│         │                                   │
│         │          ┌──────────────┐       │
│         │          │              │       │
│         └──────────│    Redis     │       │
│                    │    Cache     │       │
│                    │  (Port 6379) │       │
│                    │              │       │
│                    └──────────────┘       │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 📁 Volumes & Persistence

### Persistent Data:

- **PostgreSQL**: `postgres_data` volume
- **Redis**: `redis_data` volume
- **Application Data**: `./data` directory mounted

### Mounted Directories:

```
./data         → /app/data          (uploads, exports)
./checkpoints  → /app/checkpoints   (model weights)
./logs         → /app/logs          (application logs)
```

---

## 🔧 Configuration

### Environment Variables

Edit `.env` file oder `docker-compose.yml`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://mindbridge:PASSWORD@postgres:5432/mindbridge

# Redis
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-super-secret-key-here

# Environment
ENVIRONMENT=development  # or production
```

### Production Settings

Für Production-Deployment:

1. **Ändern Sie Passwords** in `docker-compose.yml`
2. **Setzen Sie SECRET_KEY** auf einen sicheren Wert
3. **Environment** auf `production` setzen
4. **Deaktivieren Sie pgAdmin** (remove `--profile tools`)

---

## 🚀 Deployment Workflows

### Development

```bash
# Start services
./docker.sh start

# Watch logs
./docker.sh logs -f api

# Make code changes (hot reload active)

# Restart if needed
./docker.sh restart api
```

### Production

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d

# Check health
curl http://your-domain.com/ping
```

---

## 🧪 Testing

### Run Tests in Container

```bash
# pytest
./docker.sh exec pytest tests/

# Coverage
./docker.sh exec pytest --cov=src tests/

# Specific test
./docker.sh exec pytest tests/test_api.py::test_health_check
```

---

## 📊 Monitoring

### View Logs

```bash
# All services
./docker.sh logs

# Specific service
./docker.sh logs api
./docker.sh logs postgres
./docker.sh logs redis

# Follow logs (live)
./docker.sh logs -f api
```

### Container Stats

```bash
# Resource usage
docker stats

# Disk usage
docker system df
```

---

## 🔍 Troubleshooting

### Container won't start

```bash
# Check logs
./docker.sh logs api

# Check status
./docker.sh status

# Rebuild
./docker.sh build
```

### Database connection issues

```bash
# Check PostgreSQL logs
./docker.sh logs postgres

# Test connection
./docker.sh exec psql $DATABASE_URL

# Reset database
./docker.sh stop
./docker.sh clean  # WARNING: Deletes all data!
./docker.sh start
./docker.sh db-setup
```

### Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

### Clean slate

```bash
# Remove everything and start fresh
./docker.sh clean
./docker.sh build
./docker.sh start
./docker.sh db-setup
```

---

## 🎓 Training in Docker

### Generate Training Data

```bash
# Generate sample data
./docker.sh exec python -m src.ai.training.data.sample_data_generator

# Generate multilingual data
./docker.sh exec python -c "from src.ai.training.data.multilingual import create_multilingual_data; create_multilingual_data()"
```

### Run Training

```bash
# Start training (placeholder for training script)
./docker.sh exec python train.py --model sentiment --epochs 10
```

---

## 💡 Tips & Best Practices

1. **Always use `./docker.sh` commands** - easier than raw docker-compose
2. **Check logs regularly** - `./docker.sh logs -f api`
3. **Backup database** before major changes
4. **Use volumes** for persistent data
5. **Set proper secrets** in production

---

## 🆘 Need Help?

```bash
# Show all commands
./docker.sh help

# Check Docker status
docker info

# Check running containers
docker ps

# View all containers (including stopped)
docker ps -a
```

---

## 📖 Next Steps

1. ✅ Start services: `./docker.sh start`
2. ✅ Open API docs: http://localhost:8000/docs
3. ✅ Register a user via API
4. ✅ Create mood entries
5. ✅ Test AI endpoints

**Happy coding! 🚀**
