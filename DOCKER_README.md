# 🐳 Docker Quick Start

## Schnellstart (2 Befehle)

```bash
# 1. Container starten
docker-compose up -d

# 2. Logs anschauen
docker-compose logs -f
```

**Zugriff:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Verfügbare Services

- **postgres** - PostgreSQL 15 Datenbank (Port 5432)
- **redis** - Redis Cache (Port 6379)
- **backend** - FastAPI Backend (Port 8000)
- **frontend** - Next.js Frontend (Port 3000)
- **pgadmin** - DB Management UI (Port 5050, optional)

## Häufige Befehle

```bash
# Services starten
docker-compose up -d

# Services stoppen
docker-compose down

# Neu bauen nach Code-Änderungen
docker-compose up -d --build

# Logs anschauen
docker-compose logs -f backend
docker-compose logs -f frontend

# AI Models trainieren
docker-compose exec backend python -m src.ai.training.trainer --all

# In Backend Shell
docker-compose exec backend bash

# Datenbank Migrations
docker-compose exec backend alembic upgrade head

# Datenbank Backup
docker-compose exec postgres pg_dump -U mindbridge_user mindbridge_db > backup.sql
```

## Troubleshooting

### Container startet und stoppt sofort
```bash
# Logs prüfen
docker-compose logs backend
docker-compose logs frontend
```

### Port schon belegt
```bash
# Anderen Port nutzen - in docker-compose.yml ändern:
backend:
  ports:
    - "8001:8000"  # statt 8000:8000
```

### Database connection failed
```bash
# Postgres warten lassen
docker-compose up -d postgres
sleep 10
docker-compose up -d backend
```

### AI Models nicht gefunden
```bash
# Models trainieren
docker-compose exec backend python -m src.ai.training.data.sample_data_generator
docker-compose exec backend python -m src.ai.training.trainer --all
```

## Cleanup

```bash
# Alles stoppen und entfernen
docker-compose down

# Inkl. Volumes (⚠️ Daten gehen verloren!)
docker-compose down -v

# System cleanup
docker system prune -a
```

## Production

Siehe `docs/PRODUCTION_DEPLOYMENT.md` für Production-Setup.
