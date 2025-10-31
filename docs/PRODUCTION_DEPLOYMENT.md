# Production Deployment Guide

## 🚀 Quick Production Deployment

This guide covers deploying the MindBridge AI Platform to production.

## Prerequisites

### Required
- Docker and Docker Compose (20.10+)
- PostgreSQL 15+ database
- Domain with SSL certificate
- At least 2GB RAM, 2 CPU cores
- 20GB disk space

### Recommended
- Kubernetes cluster (for high availability)
- Redis for caching
- Nginx/Traefik for reverse proxy
- Monitoring (Prometheus, Grafana)
- Log aggregation (ELK stack or similar)

## 🔒 Security Checklist

Before deploying to production, ensure:

- [ ] Strong `SECRET_KEY` generated (minimum 32 random characters)
- [ ] Database uses strong passwords
- [ ] HTTPS enabled (`HTTPS_ONLY=true`)
- [ ] `DEBUG=false`
- [ ] Specific `ALLOWED_HOSTS` and `CORS_ORIGINS` (no wildcards)
- [ ] Rate limiting enabled
- [ ] Email verification enabled
- [ ] Firewall configured (only ports 80/443 open)
- [ ] Database backups configured
- [ ] SSL certificates valid and auto-renewing
- [ ] Environment variables stored securely (not in git)

## 📋 Step-by-Step Deployment

### 1. Prepare Environment

```bash
# Clone repository
git clone https://github.com/YourOrg/MentalHealth.git
cd MentalHealth

# Copy production environment template
cp .env.production.example .env

# Generate strong secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy output to .env as SECRET_KEY

# Edit .env with your production values
nano .env
```

### 2. Update Configuration

Edit `.env` file with your production values:

```env
# CRITICAL: Replace these values!
SECRET_KEY=your-generated-secret-key-here
DATABASE_URL=postgresql://user:password@postgres:5432/mindbridge_db
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
HTTPS_ONLY=true
DEBUG=false
ENVIRONMENT=production

# Email configuration (required for production)
SMTP_HOST=smtp.sendgrid.net
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=noreply@yourdomain.com
EMAIL_VERIFICATION_REQUIRED=true

# Optional: Add monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

### 3. Database Setup

```bash
# Option A: Using Docker Compose (included PostgreSQL)
docker-compose -f docker-compose.prod.yml up -d postgres

# Option B: Using external PostgreSQL
# Create database manually:
psql -h your-db-host -U postgres
CREATE DATABASE mindbridge_db;
CREATE USER mindbridge_user WITH ENCRYPTED PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE mindbridge_db TO mindbridge_user;
```

### 4. Initialize AI Models

```bash
# Generate sample training data and train models
docker-compose -f docker-compose.prod.yml run --rm backend python -m src.ai.training.data.sample_data_generator
docker-compose -f docker-compose.prod.yml run --rm backend python -m src.ai.training.trainer --all

# Or copy pre-trained models to data/models/
```

### 5. Deploy Application

#### Option A: Docker Compose (Recommended for single server)

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### Option B: Kubernetes (Recommended for clusters)

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmaps.yaml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/redis/
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/ingress/

# Check status
kubectl get pods -n mindbridge
kubectl logs -n mindbridge -l app=backend
```

### 6. Configure Reverse Proxy

#### Nginx Configuration

```nginx
# /etc/nginx/sites-available/mindbridge

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long AI requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # File uploads
    client_max_body_size 10M;
}
```

Enable site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/mindbridge /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 7. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal:
sudo certbot renew --dry-run
```

### 8. Health Checks

```bash
# Check backend health
curl https://yourdomain.com/api/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-31T...",
  "services": {
    "database": "connected",
    "ai_engine": "initialized"
  }
}

# Check frontend
curl https://yourdomain.com/

# Check API docs (should be disabled in production)
curl https://yourdomain.com/docs
# Expected: 404 or redirect
```

## 🔄 Updates and Maintenance

### Deploy Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Database Backups

```bash
# Create backup script
cat > /opt/mindbridge/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/mindbridge"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U mindbridge_user mindbridge_db | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"
# Keep only last 30 days
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +30 -delete
EOF

chmod +x /opt/mindbridge/backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /opt/mindbridge/backup.sh" | crontab -
```

### Monitoring

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Check resource usage
docker stats

# Database size
docker-compose -f docker-compose.prod.yml exec postgres psql -U mindbridge_user -d mindbridge_db -c "SELECT pg_size_pretty(pg_database_size('mindbridge_db'));"
```

## 🚨 Troubleshooting

### Backend won't start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs backend

# Common issues:
# 1. Database not ready: Wait 30 seconds and restart
# 2. Missing SECRET_KEY: Check .env file
# 3. Database connection failed: Verify DATABASE_URL
```

### AI models not loading

```bash
# Verify model files exist
docker-compose -f docker-compose.prod.yml exec backend ls -lh /app/data/models/

# Expected files:
# - tokenizer.pkl
# - emotion_classifier.pt
# - mood_predictor.pt
# - chat_generator.pt

# Retrain if missing
docker-compose -f docker-compose.prod.yml exec backend python -m src.ai.training.trainer --all
```

### High CPU/Memory usage

```bash
# Check AI device setting
# CPU mode uses less resources but is slower
AI_DEVICE=cpu

# Reduce model complexity
HIDDEN_DIM=128  # Default: 256
NUM_LAYERS=1    # Default: 2
```

### Database connection pool exhausted

```bash
# Increase pool size in database.py or via environment
DATABASE_POOL_SIZE=20  # Default: 10
DATABASE_MAX_OVERFLOW=40  # Default: 20
```

## 📊 Performance Optimization

### Enable Redis Caching

```yaml
# docker-compose.prod.yml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass your-redis-password
    volumes:
      - redis_data:/data
```

### Database Indexing

```sql
-- Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U mindbridge_user -d mindbridge_db

-- Add indexes for common queries
CREATE INDEX idx_mood_user_created ON mood_entries(user_id, created_at DESC);
CREATE INDEX idx_dreams_user_created ON dream_entries(user_id, created_at DESC);
CREATE INDEX idx_users_email ON users(email);
```

### Frontend CDN

Use a CDN for frontend static assets:
- Cloudflare
- AWS CloudFront
- Netlify

## 🔐 Security Hardening

### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -j DROP
```

### Fail2ban for Brute Force Protection

```bash
# Install fail2ban
sudo apt install fail2ban

# Configure for nginx
sudo nano /etc/fail2ban/jail.local
```

```ini
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https"]
logpath = /var/log/nginx/error.log
findtime = 600
bantime = 7200
maxretry = 10
```

### Regular Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d

# Update dependencies
pip install --upgrade -r requirements.txt
```

## 📱 Monitoring and Alerts

### Prometheus + Grafana

See `docs/MONITORING.md` for complete setup.

### Uptime Monitoring

Use external services:
- UptimeRobot (free)
- Pingdom
- StatusCake

### Log Aggregation

Configure Sentry for error tracking:

```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
```

## 🎯 Production Checklist

Before going live:

- [ ] Environment variables secured
- [ ] SSL certificate installed and auto-renewing
- [ ] Database backups automated
- [ ] Monitoring and alerts configured
- [ ] Log aggregation setup
- [ ] Firewall configured
- [ ] Rate limiting tested
- [ ] Load testing completed
- [ ] Disaster recovery plan documented
- [ ] Security audit completed
- [ ] GDPR compliance verified
- [ ] Privacy policy and terms of service published
- [ ] User data export/deletion tested
- [ ] Email delivery tested
- [ ] AI models trained on production data
- [ ] Performance benchmarks met
- [ ] Documentation up to date

## 📚 Additional Resources

- [Kubernetes Deployment](./KUBERNETES.md)
- [Monitoring Setup](./MONITORING.md)
- [Backup & Recovery](./BACKUP_RECOVERY.md)
- [Security Best Practices](./SECURITY.md)
- [API Documentation](./API.md)

## 🆘 Support

For production support:
- Email: support@mindbridge.app
- Security issues: security@mindbridge.app
- GitHub Issues: https://github.com/YourOrg/MentalHealth/issues
