# Container Neustart Anleitung

## Problem
Der Backend-Container läuft noch auf Port 8000 statt 8080, obwohl die Konfiguration korrekt ist.

## Ursache
Der Container läuft noch mit der alten Version des Codes vor den Port-Änderungen.

## Lösung: Container neu bauen und starten

### Option 1: Kompletter Neustart mit Rebuild (empfohlen)
```bash
# Stoppe alle Container
docker-compose -f docker-compose.full.yaml down

# Lösche alte Images (optional, aber empfohlen für sauberen Build)
docker-compose -f docker-compose.full.yaml down --rmi local

# Baue alle Images neu und starte Container
docker-compose -f docker-compose.full.yaml up --build -d

# Überprüfe die Logs
docker-compose -f docker-compose.full.yaml logs backend | grep "Uvicorn running"
```

Sie sollten jetzt sehen:
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Option 2: Nur Backend neu bauen
```bash
# Stoppe nur Backend-Container
docker-compose -f docker-compose.full.yaml stop backend

# Entferne Backend-Container
docker-compose -f docker-compose.full.yaml rm -f backend

# Baue Backend neu
docker-compose -f docker-compose.full.yaml build --no-cache backend

# Starte Backend
docker-compose -f docker-compose.full.yaml up -d backend

# Überprüfe Logs
docker-compose -f docker-compose.full.yaml logs -f backend
```

### Überprüfung nach dem Neustart

1. **Backend-Port überprüfen:**
```bash
docker-compose -f docker-compose.full.yaml logs backend | grep "Uvicorn running"
```
Erwartetes Ergebnis: `http://0.0.0.0:8080`

2. **Container-Status überprüfen:**
```bash
docker-compose -f docker-compose.full.yaml ps
```
Backend sollte unter Port `0.0.0.0:8080->8080/tcp` laufen

3. **Health-Check überprüfen:**
```bash
curl http://localhost:8080/health
```
Sollte JSON-Antwort zurückgeben

4. **API-Dokumentation testen:**
```bash
curl http://localhost:8080/docs
```
Sollte HTML zurückgeben (Swagger UI)

## Wichtig
Nach dem Neustart:
- Backend läuft auf Port 8080 ✓
- Frontend kann mit Backend kommunizieren über `http://backend:8080` ✓
- Von außen erreichbar über `http://localhost:8080` ✓
- Frontend-Proxy leitet `/api/*` weiter an Backend ✓

## Troubleshooting

### Container startet nicht
```bash
# Ausführliche Logs anzeigen
docker-compose -f docker-compose.full.yaml logs --tail=100 backend

# Container-Konfiguration überprüfen
docker inspect mentalhealth-backend | grep -A 5 "Env"
```

### Port-Konflikt
Wenn Port 8080 bereits belegt ist:
```bash
# Überprüfe welcher Prozess Port 8080 nutzt
sudo lsof -i :8080
# oder
sudo netstat -tlnp | grep :8080

# Stoppe den anderen Prozess oder ändere den Port in docker-compose.full.yaml
```

### Alte Images löschen
```bash
# Alle ungenutzten Images entfernen
docker image prune -a

# Spezifisch MentalHealth-Images löschen
docker images | grep mentalhealth | awk '{print $3}' | xargs docker rmi -f
```
