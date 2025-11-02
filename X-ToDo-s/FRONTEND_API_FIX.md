# Frontend API Connection Fix

## 🐛 Problem

```
POST http://localhost:8080/api/v1/users/register/patient net::ERR_CONNECTION_REFUSED
```

### Ursache:
- Next.js `NEXT_PUBLIC_*` Variablen werden zur **BUILD-TIME** eingebrannt
- Docker Compose hatte `NEXT_PUBLIC_API_URL: http://backend:8080`  
- Das funktioniert NUR im Docker-Netzwerk, NICHT im Browser!
- Browser kann `backend` nicht auflösen → Connection Refused

## ✅ Lösung

### Was wurde geändert:

**1. `docker-compose.full.yaml`:**
```yaml
frontend:
  build:
    args:
      # BUILD-TIME Variables - werden in den JavaScript-Code eingebaut
      NEXT_PUBLIC_API_URL: http://localhost:8080  # ← FÜR BROWSER!
      NEXT_PUBLIC_API_VERSION: v1
  environment:
    # Zusätzlich: Internal URL für Server-Side Calls
    INTERNAL_API_URL: http://backend:8080  # ← FÜR SSR
```

**2. `frontend/Dockerfile`:**
```dockerfile
# Build-Args akzeptieren
ARG NEXT_PUBLIC_API_URL=http://localhost:8080
ARG NEXT_PUBLIC_API_VERSION=v1

# Als ENV verfügbar machen beim Build
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_VERSION=$NEXT_PUBLIC_API_VERSION
```

**3. `frontend/.env.local` (NEU):**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_API_VERSION=v1
```

## 🚀 Nach dem Merge - SO BEHEBEN SIE ES:

### **WICHTIG: Frontend muss NEU GEBAUT werden!**

```bash
# 1. Merge den Pull Request auf GitHub

# 2. Pull die Änderungen
git checkout main
git pull

# 3. Container stoppen
docker-compose -f docker-compose.full.yaml down

# 4. Frontend NEU BAUEN (wichtig!)
docker-compose -f docker-compose.full.yaml build --no-cache frontend

# 5. Alles starten
docker-compose -f docker-compose.full.yaml up -d

# 6. Logs prüfen
docker logs -f mentalhealth-frontend
```

## 🧪 Verifizierung

### 1. **Prüfen Sie, ob Backend läuft:**
```bash
curl http://localhost:8080/health
# Sollte: {"status":"healthy"} zurückgeben
```

### 2. **Prüfen Sie Frontend-Logs:**
```bash
docker logs mentalhealth-frontend
# Sollte keine "ERR_CONNECTION_REFUSED" Fehler zeigen
```

### 3. **Prüfen Sie im Browser:**
- Öffnen: http://localhost:3000
- DevTools (F12) → Network Tab
- API-Calls sollten zu `http://localhost:8080/api/v1/...` gehen
- Status sollte 200 oder 201 sein (NICHT ERR_CONNECTION_REFUSED)

## 📋 Warum passiert das?

### Next.js Build-Time vs Runtime:

```javascript
// Zur BUILD-TIME:
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

// Wird zu:
const API_URL = 'http://localhost:8080';  // ← Fest eingebrannt!
```

**Das bedeutet:**
- Wenn Sie `NEXT_PUBLIC_API_URL` ändern, müssen Sie **neu bauen**
- `environment:` in docker-compose wirkt NUR zur Runtime (zu spät!)
- `build.args:` in docker-compose wirkt zur BUILD-TIME (richtig!)

## 🎯 Checkliste nach dem Fix:

- [ ] Pull Request gemerged
- [ ] `git pull` ausgeführt
- [ ] Frontend **neu gebaut** (`--no-cache` wichtig!)
- [ ] Container gestartet
- [ ] Backend erreichbar unter http://localhost:8080/health
- [ ] Frontend lädt ohne Connection-Fehler
- [ ] Login funktioniert
- [ ] API-Calls im Browser zeigen richtigen Port

## 🔍 Troubleshooting

### "Immer noch ERR_CONNECTION_REFUSED"

1. **Backend prüfen:**
   ```bash
   docker ps | grep backend
   # Sollte laufen und Port 8080:8080 zeigen
   ```

2. **Port-Test:**
   ```bash
   curl http://localhost:8080/health
   # MUSS funktionieren!
   ```

3. **Frontend neu bauen (mit --no-cache!):**
   ```bash
   docker-compose -f docker-compose.full.yaml build --no-cache frontend
   ```

4. **Browser-Cache leeren:**
   - Chrome: Strg+Shift+Delete
   - Firefox: Strg+Shift+Delete
   - Oder Inkognito-Modus verwenden

### "Backend läuft, aber Frontend verbindet nicht"

```bash
# Frontend-Container prüfen
docker exec -it mentalhealth-frontend sh

# Im Container:
cat /app/.env.local  # Sollte existieren
printenv | grep NEXT_PUBLIC  # Sollte richtige URL zeigen
```

## 💡 Best Practice für Zukunft:

**Lokale Entwicklung (ohne Docker):**
```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8080
```

**Docker Development:**
```yaml
# docker-compose.yaml
build:
  args:
    NEXT_PUBLIC_API_URL: http://localhost:8080
```

**Docker Production:**
```yaml
build:
  args:
    NEXT_PUBLIC_API_URL: https://api.ihre-domain.de
```

---

**Nach diesem Fix sollte alles funktionieren!** 🎉
