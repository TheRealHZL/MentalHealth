# 🧪 Testing Guide - MentalHealth Platform

Complete guide for testing the application at all levels.

## Table of Contents

1. [Local Testing](#local-testing)
2. [API Testing](#api-testing)
3. [Frontend Testing](#frontend-testing)
4. [Integration Testing](#integration-testing)
5. [Load Testing](#load-testing)
6. [Security Testing](#security-testing)

---

## Local Testing

### Quick Test Suite

```bash
# Run all tests
docker-compose -f docker-compose.full.yaml exec backend pytest

# With coverage
docker-compose -f docker-compose.full.yaml exec backend pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Test Specific Components

```bash
# API tests only
pytest tests/api/

# Database tests only
pytest tests/database/

# AI service tests only
pytest tests/ai/

# Security tests only
pytest tests/security/
```

---

## API Testing

### Using cURL

#### Health Check

```bash
# Backend health
curl http://localhost:8000/health

# Should return:
# {"status": "healthy", "database": "connected", "redis": "connected"}
```

#### Authentication

```bash
# Register new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Save the token from response
TOKEN="<your-token-here>"

# Use authenticated endpoint
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"
```

#### Chat/AI Session

```bash
# Create session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Send message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<session-id>",
    "message": "I feel anxious today"
  }'
```

### Using Postman

1. Import the Postman collection (if provided)
2. Set environment variables:
   - `base_url`: http://localhost:8000
   - `token`: (obtained from login)
3. Run collection tests

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "full_name": "Test User"
    }
)
print(response.json())

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }
)
token = response.json()["access_token"]

# Use token
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/users/me", headers=headers)
print(response.json())
```

---

## Frontend Testing

### Manual Testing Checklist

- [ ] Home page loads
- [ ] Registration flow works
- [ ] Login/logout works
- [ ] Dashboard displays correctly
- [ ] Chat interface functional
- [ ] Profile update works
- [ ] Settings page accessible
- [ ] Responsive design (mobile/tablet)
- [ ] Error handling displays properly

### Browser Testing

Test in multiple browsers:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Accessibility Testing

```bash
# Install axe-core
npm install -g @axe-core/cli

# Run accessibility audit
cd frontend
axe http://localhost:3000
```

---

## Integration Testing

### Full Stack Test

```bash
# Start all services
docker-compose -f docker-compose.full.yaml up -d

# Wait for healthy
sleep 30

# Run integration tests
pytest tests/integration/ -v

# Test flow: Register → Login → Chat → Logout
pytest tests/integration/test_user_flow.py -v
```

### Database Integration

```bash
# Test database operations
pytest tests/integration/test_database.py -v

# Test migrations
docker-compose -f docker-compose.full.yaml exec backend alembic upgrade head
docker-compose -f docker-compose.full.yaml exec backend alembic downgrade -1
docker-compose -f docker-compose.full.yaml exec backend alembic upgrade head
```

### Redis Integration

```bash
# Test caching
pytest tests/integration/test_cache.py -v

# Manual Redis test
docker-compose -f docker-compose.full.yaml exec redis redis-cli
> PING
> SET test "hello"
> GET test
> DEL test
> EXIT
```

---

## Load Testing

### Using Apache Bench

```bash
# Install ab
brew install httpd  # macOS
apt-get install apache2-utils  # Ubuntu

# Test endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# With authentication
ab -n 1000 -c 10 -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/users/me
```

### Using Locust

```bash
# Install
pip install locust

# Create locustfile.py
cat > locustfile.py << 'EOF'
from locust import HttpUser, task, between

class MentalHealthUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePassword123!"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def view_dashboard(self):
        self.client.get("/api/v1/users/me", headers=self.headers)

    @task(1)
    def send_message(self):
        self.client.post("/api/v1/chat", headers=self.headers, json={
            "message": "Test message"
        })
EOF

# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

Open http://localhost:8089 to configure and start the test.

### Performance Benchmarks

Target metrics:
- **API Response Time**: < 200ms (p95)
- **Chat Response Time**: < 2s (p95)
- **Throughput**: > 100 req/s
- **Error Rate**: < 1%

---

## Security Testing

### OWASP Top 10 Testing

#### 1. SQL Injection

```bash
# Test with malicious input
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com OR 1=1--",
    "password": "anything"
  }'

# Should return error, not succeed
```

#### 2. XSS (Cross-Site Scripting)

```bash
# Test with script tags
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "<script>alert(\"XSS\")</script>"
  }'

# Should be sanitized in response
```

#### 3. Authentication Bypass

```bash
# Test without token
curl http://localhost:8000/api/v1/users/me

# Should return 401 Unauthorized

# Test with invalid token
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer invalid-token"

# Should return 401 Unauthorized
```

#### 4. Rate Limiting

```bash
# Send many requests quickly
for i in {1..150}; do
  curl http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"wrong"}' &
done
wait

# Should see 429 Too Many Requests after limit
```

### Using OWASP ZAP

```bash
# Install ZAP
brew install --cask owasp-zap  # macOS

# Or download from https://www.zaproxy.org/

# Run automated scan
zap-cli quick-scan http://localhost:8000

# Or use GUI for detailed testing
```

### Security Headers Check

```bash
# Check security headers
curl -I http://localhost:8000/

# Should include:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Strict-Transport-Security: max-age=31536000
```

### SSL/TLS Testing

```bash
# Test SSL configuration (production only)
nmap --script ssl-enum-ciphers -p 443 mentalhealth.example.com

# Or use SSL Labs
# https://www.ssllabs.com/ssltest/
```

---

## Automated Testing in CI/CD

Tests run automatically on:
- Every push to feature branches
- Pull requests to main/develop
- Nightly security scans

### View Test Results

1. Go to GitHub Actions tab
2. Click on latest workflow run
3. View test results and coverage

### Local CI Simulation

```bash
# Run the same tests as CI
docker-compose -f docker-compose.full.yaml up -d

# Backend tests
docker-compose -f docker-compose.full.yaml exec backend pytest -v --cov=src

# Frontend build test
docker-compose -f docker-compose.full.yaml exec frontend npm run build

# Security scan
docker run --rm -v $(pwd):/src returntocorp/semgrep semgrep --config=auto /src
```

---

## Test Data Management

### Seed Test Data

```bash
# Create test users and data
docker-compose -f docker-compose.full.yaml exec backend python scripts/seed_data.py

# Reset database
docker-compose -f docker-compose.full.yaml down -v
docker-compose -f docker-compose.full.yaml up -d
docker-compose -f docker-compose.full.yaml exec backend alembic upgrade head
```

### Test Data Fixtures

```python
# tests/conftest.py
import pytest

@pytest.fixture
def test_user(db_session):
    user = User(
        email="test@example.com",
        full_name="Test User"
    )
    user.set_password("SecurePassword123!")
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}
```

---

## Monitoring Test Results

### Prometheus Metrics

```bash
# Check metrics endpoint
curl http://localhost:8000/metrics

# View in Prometheus
open http://localhost:9090
```

Key metrics:
- `http_requests_total` - Total requests
- `http_request_duration_seconds` - Response time
- `http_requests_errors_total` - Error count
- `db_connections_active` - Database connections

### Grafana Dashboards

```bash
# Start with monitoring profile
docker-compose -f docker-compose.full.yaml --profile monitoring up -d

# Access Grafana
open http://localhost:3001
# Login: admin/admin
```

---

## Test Environment Cleanup

```bash
# Stop all services
docker-compose -f docker-compose.full.yaml down

# Remove all data
docker-compose -f docker-compose.full.yaml down -v

# Remove images
docker rmi mentalhealth/backend mentalhealth/frontend

# Clean Docker cache
docker system prune -a
```

---

## Best Practices

1. **Write Tests First** - TDD approach
2. **Test in Isolation** - Mock external dependencies
3. **Use Fixtures** - Reusable test data
4. **Clean Up** - Reset state between tests
5. **Meaningful Names** - Clear test descriptions
6. **Fast Tests** - Keep unit tests under 100ms
7. **CI Integration** - Tests run on every commit
8. **Coverage Goal** - Aim for >80% code coverage
9. **Security Tests** - Include in every PR
10. **Document Tests** - Explain complex test scenarios

---

## Troubleshooting Tests

### Tests Failing Locally

```bash
# Clear cache
pytest --cache-clear

# Run with verbose output
pytest -vv

# Run specific test
pytest tests/api/test_auth.py::test_login -vv

# Debug mode
pytest --pdb
```

### Database Issues

```bash
# Reset test database
docker-compose -f docker-compose.full.yaml exec postgres dropdb -U mentalhealth test_db
docker-compose -f docker-compose.full.yaml exec postgres createdb -U mentalhealth test_db
```

### Port Conflicts

```bash
# Change test ports in docker-compose.test.yaml
# Or kill processes using ports
lsof -ti:8000 | xargs kill -9
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [Locust Documentation](https://docs.locust.io/)

---

**Happy Testing! 🧪**
