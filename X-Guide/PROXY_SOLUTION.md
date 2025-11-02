# ✅ DIE RICHTIGE LÖSUNG: Next.js Proxy

## 🎯 Ihr Einwand war absolut richtig!

> "Warum localhost? Wir sind in einer Docker-Umgebung!"

**Sie hatten Recht!** Die Lösung ist **NICHT** `localhost`, sondern ein **Proxy**!

## 🏗️ Wie es jetzt funktioniert:

```
┌─────────────────────────────────────────────────────────────┐
│                    Ihr Computer (Host)                      │
│                                                             │
│  ┌──────────────┐                                          │
│  │   Browser    │                                          │
│  │              │                                          │
│  │  GET /api/v1/users/login  ←─── Relative URL!           │
│  └──────┬───────┘                                          │
│         │                                                  │
│         ↓ http://localhost:3000/api/v1/...                │
└─────────┼────────────────────────────────────────────────┘
          │
          │ Docker Port-Mapping 3000:3000
          │
┌─────────┼────────────────────────────────────────────────┐
│         │        Docker Container: mentalhealth-frontend  │
│         ↓                                                  │
│  ┌─────────────────┐                                      │
│  │  Next.js Server │                                      │
│  │  (läuft in     │                                      │
│  │   Container!)  │                                      │
│  │                │                                      │
│  │  Proxy Rewrite:│                                      │
│  │  /api/* →      │─────────┐                            │
│  └────────────────┘          │                            │
│                              │                            │
│                              │ http://backend:8080/api/*  │
│                              │ (Container-zu-Container!)  │
└──────────────────────────────┼────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────┼────────────────────────────┐
│                              │   Docker Container: backend │
│                     ┌────────▼────────┐                   │
│                     │   FastAPI       │                   │
│                     │   Port 8080     │                   │
│                     └─────────────────┘                   │
└───────────────────────────────────────────────────────────┘
```

## 📝 Was wurde geändert:

### 1. **Frontend verwendet relative URLs**

**frontend/lib/api.ts:**
```typescript
// VORHER (falsch):
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
const BASE_URL = `${API_URL}/api/${API_VERSION}`;

// NACHHER (richtig):
const BASE_URL = `/api/${API_VERSION}`;  // Relativ!
```

### 2. **Next.js proxied zum Backend**

**frontend/next.config.js:**
```javascript
async rewrites() {
  const apiUrl = process.env.INTERNAL_API_URL || 'http://backend:8080';
  
  return [
    {
      source: '/api/:path*',
      destination: `${apiUrl}/api/:path*`,  // → http://backend:8080
    },
  ]
}
```

### 3. **Docker Compose konfiguriert**

**docker-compose.full.yaml:**
```yaml
frontend:
  environment:
    # Runtime: Next.js server verwendet diese URL für Proxy
    INTERNAL_API_URL: http://backend:8080  # ← Container-zu-Container!
```

## ✅ Vorteile dieser Lösung:

1. **Browser muss Backend nie direkt erreichen** ✅
   - Keine CORS-Probleme
   - Keine mixed-content Probleme (HTTP/HTTPS)
   
2. **Funktioniert in jeder Umgebung** ✅
   - Docker: `http://backend:8080`
   - Lokal: `http://localhost:8080` (via INTERNAL_API_URL)
   - Produktion: `https://api.ihre-domain.de`

3. **Keine Build-Time-Probleme** ✅
   - Kein `NEXT_PUBLIC_API_URL` mehr nötig
   - Proxy-URL ist Runtime-konfigurierbar

4. **Sicher und sauber** ✅
   - Backend ist nicht direkt vom Browser erreichbar
   - Alle Requests gehen durch Next.js Server

## 🚀 Nach dem Merge:

```bash
# 1. Pull Request mergen

# 2. Code pullen
git checkout main
git pull

# 3. Frontend NEU BAUEN
docker-compose -f docker-compose.full.yaml build --no-cache frontend

# 4. Starten
docker-compose -f docker-compose.full.yaml up -d

# 5. Testen
curl http://localhost:3000  # Frontend
# Im Browser: http://localhost:3000
# API-Calls gehen jetzt zu: /api/v1/... (relativ!)
```

## 🧪 Wie Sie es verifizieren:

**Im Browser (F12 → Network Tab):**
```
Request URL: http://localhost:3000/api/v1/users/login
             ^^^^^^^^^^^^^^^^^^^^^ Frontend URL!
             Nicht mehr http://localhost:8080!
```

**Next.js proxied intern:**
```
Browser → http://localhost:3000/api/v1/users/login
          ↓ (Next.js Proxy)
Docker  → http://backend:8080/api/v1/users/login
```

## 💡 Best Practice:

**Lokale Entwicklung:**
```bash
# .env.local
INTERNAL_API_URL=http://localhost:8080
```

**Docker Development:**
```yaml
# docker-compose.yaml
environment:
  INTERNAL_API_URL: http://backend:8080
```

**Production:**
```yaml
environment:
  INTERNAL_API_URL: https://api.ihre-domain.de
```

---

**Das ist die professionelle Lösung!** 🎉

Kein hardcoded `localhost` mehr, alles läuft über den Proxy!
