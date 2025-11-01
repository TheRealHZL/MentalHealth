# Admin-Zugang - Anleitung

## 🔐 Standard Admin-Credentials

**Default-Admin (nach Installation):**
```
Email:    admin@mentalhealth.com
Username: admin
Password: admin123
```

⚠️ **WICHTIG:** Diese Credentials nach dem ersten Login sofort ändern!

---

## 🚀 Schnellstart

### 1. Mit Default-Credentials anmelden

**Browser (Frontend):**
```
http://localhost:3000/login
```

**API (Swagger Docs):**
```
http://localhost:8080/docs
```

**curl (Terminal):**
```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@mentalhealth.com",
    "password": "admin123"
  }'
```

---

## 🛠️ Admin-User verwalten

### Mit dem `create_admin.py` Script

**Alle Admin-User auflisten:**
```bash
python create_admin.py list
```

**Neuen Admin-User erstellen:**
```bash
python create_admin.py create myadmin@example.com MySecurePass123

# Mit Namen:
python create_admin.py create myadmin@example.com MySecurePass123 Max Mustermann
```

**Beispiel-Output:**
```
✅ Admin-User erfolgreich erstellt!

📧 Email:    myadmin@example.com
🔑 Passwort: MySecurePass123
👤 Name:     Max Mustermann

🔐 Login-URL: http://localhost:8080/docs
🌐 Frontend:  http://localhost:3000/login
```

---

## 📋 Alternative Methoden

### 1. Setup-Script verwenden

```bash
./scripts/setup.sh
```

Das Script:
- Erkennt die Umgebung (Docker/Kubernetes/Host)
- Führt Datenbank-Migrationen aus
- Fragt nach Admin-Credentials
- Erstellt den Admin-User

### 2. Manuell in der Datenbank

**Passwort-Hash generieren:**
```bash
python3 << 'EOFPW'
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"])
print(pwd_context.hash("YourPassword123"))
EOFPW
```

**User in DB einfügen:**
```sql
-- Verbindung zur DB
docker exec -it mentalhealth-postgres psql -U mentalhealth -d mentalhealth_db

-- Admin erstellen
INSERT INTO users (
  id, email, password_hash, first_name, last_name, 
  role, is_active, is_verified, email_verified,
  registration_completed, created_at
) VALUES (
  gen_random_uuid(),
  'admin@example.com',
  '$2b$12$...',  -- Hash von oben
  'Admin',
  'User',
  'admin',
  true,
  true,
  true,
  true,
  NOW()
);
```

---

## 🔍 Troubleshooting

### Problem: "User existiert bereits"

**Prüfen, welche Admin-User existieren:**
```bash
python create_admin.py list
```

**Passwort eines existierenden Users zurücksetzen:**
```sql
-- In der Datenbank
UPDATE users 
SET password_hash = '$2b$12$...'  -- Neuer Hash
WHERE email = 'admin@mentalhealth.com';
```

### Problem: "Login funktioniert nicht"

**1. Prüfen Sie, ob der User aktiv ist:**
```sql
SELECT email, role, is_active, is_verified 
FROM users 
WHERE role = 'admin';
```

**2. Aktivieren Sie den User:**
```sql
UPDATE users 
SET is_active = true, 
    is_verified = true, 
    email_verified = true
WHERE email = 'admin@mentalhealth.com';
```

**3. Prüfen Sie die Backend-Logs:**
```bash
docker logs mentalhealth-backend | grep -i "login\|auth"
```

### Problem: "Keine Berechtigung"

Stellen Sie sicher, dass die Rolle wirklich "admin" ist:
```sql
SELECT id, email, role FROM users WHERE email = 'admin@mentalhealth.com';
```

Wenn nicht, korrigieren:
```sql
UPDATE users SET role = 'admin' WHERE email = 'admin@mentalhealth.com';
```

---

## 🔒 Sicherheits-Tipps

1. **Ändern Sie Default-Credentials sofort:**
   - Nach der Installation immer neues Passwort setzen

2. **Starke Passwörter verwenden:**
   - Mindestens 12 Zeichen
   - Groß- und Kleinbuchstaben, Zahlen, Sonderzeichen

3. **Admin-Zugang limitieren:**
   - Nicht für tägliche Aufgaben verwenden
   - Separate User-Accounts für verschiedene Personen

4. **Audit-Logging aktivieren:**
   - Alle Admin-Aktionen werden geloggt
   - Regelmäßig Logs überprüfen

---

## 📚 Admin-Funktionen

Als Admin haben Sie Zugriff auf:

- ✅ **User-Management:** Alle User sehen, bearbeiten, löschen
- ✅ **Therapeuten-Verifizierung:** Therapeuten-Anträge genehmigen/ablehnen
- ✅ **System-Monitoring:** Logs, Metriken, Health Checks
- ✅ **Daten-Export:** Berichte und Statistiken
- ✅ **AI-Training:** Modelle trainieren und deployen
- ✅ **Konfiguration:** System-Settings anpassen

---

## 🆘 Support

Falls Sie Probleme haben:

1. **Logs überprüfen:**
   ```bash
   docker logs mentalhealth-backend
   ```

2. **Datenbank-Status prüfen:**
   ```bash
   docker exec -it mentalhealth-postgres psql -U mentalhealth -d mentalhealth_db -c "SELECT COUNT(*) FROM users WHERE role='admin';"
   ```

3. **Issue erstellen:**
   - GitHub: https://github.com/TheRealHZL/MentalHealth/issues

---

**Viel Erfolg! 🚀**
