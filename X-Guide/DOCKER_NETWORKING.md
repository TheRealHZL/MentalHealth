# Docker Networking Guide

## Kommunikation zwischen Frontend und Backend

### Innerhalb von Docker (Container-zu-Container)

**Backend erreichbar über:**
- Service-Name: `http://backend:8080`
- Innerhalb des Docker-Netzwerks `mentalhealth-network`

**Frontend-Konfiguration (docker-compose.full.yaml):**
```yaml
environment:
  NEXT_PUBLIC_API_URL: http://backend:8080  # Service-Name!
```

### Von außen (Host-Computer → Container)

**Backend erreichbar über:**
- Localhost: `http://localhost:8080`
- Port-Mapping: `8080:8080`

### CORS-Konfiguration

Das Backend muss beide Zugriffswege erlauben:
```yaml
CORS_ORIGINS: http://localhost:3000,http://frontend:3000,http://backend:8080,http://localhost:8080
```

## Wichtige Punkte

### 1. Server bindet auf 0.0.0.0
```python
# src/main.py
uvicorn.run(
    "src.main:app",
    host="0.0.0.0",  # ✅ Hört auf allen Interfaces
    port=8080,
)
```

**Warum 0.0.0.0?**
- `localhost` oder `127.0.0.1` = nur lokal erreichbar
- `0.0.0.0` = von überall erreichbar (auch aus anderen Containern)

### 2. Next.js API URL

**Docker:**
```bash
NEXT_PUBLIC_API_URL=http://backend:8080  # Service-Name
```

**Lokale Entwicklung:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080  # Host
```

### 3. Health Checks

**Backend health check:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  # localhost ist OK hier, weil es innerhalb des gleichen Containers läuft
```

## Fehlersuche

### Frontend kann Backend nicht erreichen

**Symptom:** Network errors, CORS errors, Connection refused

**Lösung:**
1. Prüfe, dass Backend auf `0.0.0.0` hört ✅
2. Prüfe, dass Frontend `http://backend:8080` verwendet (in Docker)
3. Prüfe CORS-Einstellungen
4. Prüfe, dass beide Container im gleichen Netzwerk sind

**Debug-Befehle:**
```bash
# Prüfe Container-Netzwerk
docker network inspect mentalhealth-network

# Prüfe Container-IPs
docker inspect mentalhealth-backend | grep IPAddress
docker inspect mentalhealth-frontend | grep IPAddress

# Test Backend von Frontend aus
docker exec mentalhealth-frontend curl http://backend:8080/health

# Test Backend von Host
curl http://localhost:8080/health
```

### CORS-Fehler

**Symptom:** 
```
Access to fetch at 'http://backend:8080' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Lösung:**
Füge Frontend-Origin zu CORS_ORIGINS hinzu:
```yaml
CORS_ORIGINS: http://localhost:3000,http://frontend:3000
```

## Zusammenfassung

✅ **Backend:** Hört auf `0.0.0.0:8080`  
✅ **Docker API URL:** `http://backend:8080` (Service-Name)  
✅ **Lokale API URL:** `http://localhost:8080` (Host)  
✅ **CORS:** Beide Origins erlaubt  

## Test-Kommandos

```bash
# 1. Starte alle Container
docker-compose -f docker-compose.full.yaml up -d

# 2. Prüfe Backend-Logs
docker logs mentalhealth-backend

# 3. Prüfe Frontend-Logs
docker logs mentalhealth-frontend

# 4. Test Backend direkt
curl http://localhost:8080/health

# 5. Test aus Frontend-Container
docker exec mentalhealth-frontend curl http://backend:8080/health

# 6. Prüfe Container-Netzwerk
docker network inspect mentalhealth-network | grep -A 5 "mentalhealth-backend\|mentalhealth-frontend"
```
