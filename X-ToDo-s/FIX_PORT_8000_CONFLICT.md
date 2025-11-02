# Fix: Port 8000 Konflikt

## Problem
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

Docker versucht noch den **alten Port 8000** zu verwenden, obwohl die Konfiguration korrekt auf Port 8080 geändert wurde.

## Ursache
Es existieren noch alte Container oder Images, die Port 8000 verwenden.

## Lösung: Komplette Bereinigung

### Schritt 1: Alle Container stoppen und entfernen
```bash
# Stoppe ALLE laufenden Container (nicht nur die aus docker-compose.full.yaml)
docker stop $(docker ps -a -q) 2>/dev/null || true

# Entferne ALLE Container
docker rm $(docker ps -a -q) 2>/dev/null || true
```

### Schritt 2: Alte Images entfernen
```bash
# Entferne alle mindbridge/mentalhealth Images
docker images | grep -E "mindbridge|mentalhealth" | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

# Oder: Entferne alle ungenutzten Images
docker image prune -a -f
```

### Schritt 3: Docker-Compose bereinigen
```bash
cd ~/github/MentalHealth

# Stoppe und entferne alles von docker-compose
docker-compose -f docker-compose.full.yaml down --volumes --remove-orphans

# Noch gründlicher: auch mit altem docker-compose.yml falls vorhanden
docker-compose down --volumes --remove-orphans 2>/dev/null || true
```

### Schritt 4: Neustart mit aktuellem Code
```bash
# Stelle sicher, dass du die neuesten Änderungen hast
git pull origin claude/audit-python-project-011CUfqpiSsc9Xr35LmnkyZc

# Baue ALLES neu (ohne Cache!)
docker-compose -f docker-compose.full.yaml build --no-cache

# Starte die Container
docker-compose -f docker-compose.full.yaml up -d

# Verfolge die Logs
docker-compose -f docker-compose.full.yaml logs -f
```

### Schritt 5: Überprüfung
```bash
# 1. Überprüfe, dass Backend auf Port 8080 läuft
docker-compose -f docker-compose.full.yaml logs backend | grep "Uvicorn running"
# Erwartetes Ergebnis: "Uvicorn running on http://0.0.0.0:8080"

# 2. Überprüfe Container-Status
docker-compose -f docker-compose.full.yaml ps
# Backend sollte: 0.0.0.0:8080->8080/tcp zeigen

# 3. Teste Health-Endpoint
curl http://localhost:8080/health

# 4. Teste API-Dokumentation
curl http://localhost:8080/docs
```

## Alternative: Nur die problematischen Container entfernen

Falls Sie nur die MentalHealth-Container neu starten wollen:

```bash
# Finde alle Container
docker ps -a | grep -E "mental|mindbridge"

# Stoppe sie
docker stop mindbridge-backend mindbridge-frontend mindbridge-postgres mindbridge-redis 2>/dev/null || true

# Entferne sie
docker rm mindbridge-backend mindbridge-frontend mindbridge-postgres mindbridge-redis 2>/dev/null || true

# Entferne die Volumes (optional, löscht Datenbank!)
docker volume rm mindbridge_postgres_data mindbridge_redis_data 2>/dev/null || true

# Starte neu
docker-compose -f docker-compose.full.yaml up --build -d
```

## Wenn Port 8000 immer noch blockiert ist

Finde heraus, welcher Prozess Port 8000 verwendet:

```bash
# Auf Linux
sudo lsof -i :8000
# oder
sudo netstat -tlnp | grep :8000
# oder
sudo ss -tlnp | grep :8000

# Prozess beenden (ersetze <PID> mit der gefundenen Process ID)
sudo kill -9 <PID>
```

## Nach der Bereinigung

Ihre Container sollten jetzt korrekt laufen:
- ✅ Backend: `0.0.0.0:8080->8080/tcp`
- ✅ Frontend: `0.0.0.0:3000->3000/tcp`
- ✅ PostgreSQL: `0.0.0.0:5432->5432/tcp`
- ✅ Redis: `0.0.0.0:6379->6379/tcp`

## Troubleshooting

### "cannot remove container: container is running"
```bash
# Force stop
docker stop -t 0 <container_name>
docker rm -f <container_name>
```

### "image is being used by stopped container"
```bash
# Entferne zuerst alle Container
docker rm $(docker ps -a -q) -f
# Dann die Images
docker rmi $(docker images -q) -f
```

### Build dauert zu lange
```bash
# Verwende Build-Cache (schneller)
docker-compose -f docker-compose.full.yaml build
docker-compose -f docker-compose.full.yaml up -d
```

### Docker Disk Space voll
```bash
# Zeige Speicherverbrauch
docker system df

# Bereinige ALLES (Vorsicht: löscht alle ungenutzten Daten!)
docker system prune -a --volumes
```
