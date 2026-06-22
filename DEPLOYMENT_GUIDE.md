# Deployment Guide
## Ephemeral Intent Synthesis System

This guide covers deploying the Ephemeral Intent System to production environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring & Logging](#monitoring--logging)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Node.js**: >= 18.0.0
- **Python**: >= 3.9
- **Docker**: >= 20.10 (for containerized deployment)
- **Docker Compose**: >= 2.0
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: Minimum 10GB free space

### Required Services
- PostgreSQL or compatible database (optional, for persistence)
- Redis (optional, for caching)

---

## Local Development

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# nano .env  # or use your preferred editor

# Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# nano .env  # or use your preferred editor

# Run development server
npm run dev
```

### Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Individual Container Deployment

#### Backend Container

```bash
# Build backend image
docker build -t ephemeral-intent-backend ./backend

# Run backend container
docker run -d \
  --name ephemeral-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db:5432/ephemeral \
  -v $(pwd)/backend:/app \
  ephemeral-intent-backend
```

#### Frontend Container

```bash
# Build frontend image
docker build -t ephemeral-intent-frontend ./frontend

# Run frontend container
docker run -d \
  --name ephemeral-frontend \
  -p 3000:3000 \
  -e VITE_BACKEND_HOST=backend \
  -e VITE_BACKEND_PORT=8000 \
  ephemeral-intent-frontend
```

---

## Production Deployment

### Cloud Platforms

#### AWS Deployment

**Using ECS (Elastic Container Service)**

1. **Push Images to ECR**
```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push backend
docker tag ephemeral-intent-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ephemeral-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ephemeral-backend:latest

# Tag and push frontend
docker tag ephemeral-intent-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ephemeral-frontend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ephemeral-frontend:latest
```

2. **Create ECS Task Definition**
3. **Create ECS Service**
4. **Configure Load Balancer**
5. **Set up Auto Scaling**

#### Google Cloud Platform (GCP)

**Using Cloud Run**

```bash
# Build and deploy backend
gcloud builds submit --tag gcr.io/PROJECT_ID/ephemeral-backend ./backend
gcloud run deploy ephemeral-backend \
  --image gcr.io/PROJECT_ID/ephemeral-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

# Build and deploy frontend
gcloud builds submit --tag gcr.io/PROJECT_ID/ephemeral-frontend ./frontend
gcloud run deploy ephemeral-frontend \
  --image gcr.io/PROJECT_ID/ephemeral-frontend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Deployment

**Using Azure Container Instances**

```bash
# Create resource group
az group create --name ephemeral-rg --location eastus

# Deploy backend
az container create \
  --resource-group ephemeral-rg \
  --name ephemeral-backend \
  --image <registry>/ephemeral-backend:latest \
  --dns-name-label ephemeral-backend \
  --ports 8000

# Deploy frontend
az container create \
  --resource-group ephemeral-rg \
  --name ephemeral-frontend \
  --image <registry>/ephemeral-frontend:latest \
  --dns-name-label ephemeral-frontend \
  --ports 3000
```

### Kubernetes Deployment

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ephemeral-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ephemeral-backend
  template:
    metadata:
      labels:
        app: ephemeral-backend
    spec:
      containers:
      - name: backend
        image: ephemeral-intent-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
---
apiVersion: v1
kind: Service
metadata:
  name: ephemeral-backend-service
spec:
  selector:
    app: ephemeral-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Apply the configuration:
```bash
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml
```

---

## Environment Configuration

### Backend Environment Variables

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=info

# CORS Settings
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_ALLOW_CREDENTIALS=true

# Database (if using)
DATABASE_URL=postgresql://user:password@localhost:5432/ephemeral

# Redis (if using)
REDIS_URL=redis://localhost:6379/0

# IBM Watson (if using)
IBM_WATSON_API_KEY=your_api_key
IBM_WATSON_URL=your_watson_url

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### Frontend Environment Variables

```bash
# Backend Configuration
VITE_BACKEND_HOST=api.yourdomain.com
VITE_BACKEND_PORT=443
VITE_BACKEND_PROTOCOL=https
VITE_WS_PROTOCOL=wss

# Biometric Configuration
VITE_BIOMETRIC_DURATION=3
VITE_BIOMETRIC_FPS=30

# Feature Flags
VITE_ENABLE_VOICE=true
VITE_FEATURE_OFFLINE=true
VITE_FEATURE_ANALYTICS=true

# Analytics
VITE_ANALYTICS_ID=your-analytics-id
VITE_ANALYTICS_SAMPLE_RATE=1.0
```

---

## Monitoring & Logging

### Application Monitoring

**Using Prometheus + Grafana**

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  prometheus-data:
  grafana-data:
```

### Logging

**Centralized Logging with ELK Stack**

```bash
# Start ELK stack
docker-compose -f docker-compose.elk.yml up -d

# View logs in Kibana
# Access: http://localhost:5601
```

### Health Checks

```bash
# Backend health check
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}
```

---

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Fails

**Problem**: Frontend cannot connect to WebSocket

**Solution**:
- Check CORS settings in backend
- Verify WebSocket URL in frontend .env
- Ensure firewall allows WebSocket connections
- Check if reverse proxy supports WebSocket upgrade

```nginx
# Nginx WebSocket configuration
location /ws {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
}
```

#### 2. Biometric Capture Not Working

**Problem**: Camera access denied or MediaPipe fails

**Solution**:
- Ensure HTTPS is enabled (required for camera access)
- Check browser permissions
- Verify MediaPipe CDN is accessible
- Test with different browsers

#### 3. High Memory Usage

**Problem**: Application consuming too much memory

**Solution**:
- Implement connection pooling
- Add memory limits in Docker
- Enable garbage collection
- Monitor for memory leaks

```yaml
# Docker memory limits
services:
  backend:
    mem_limit: 2g
    mem_reservation: 1g
```

#### 4. Slow Response Times

**Problem**: API responses are slow

**Solution**:
- Enable caching (Redis)
- Optimize database queries
- Implement CDN for static assets
- Use connection pooling
- Enable compression

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Backend
DEBUG=true uvicorn app.main:app --reload

# Frontend
VITE_DEBUG_MODE=true npm run dev
```

### Performance Optimization

1. **Enable Gzip Compression**
2. **Use CDN for Static Assets**
3. **Implement Caching Strategy**
4. **Optimize Database Queries**
5. **Use Connection Pooling**
6. **Enable HTTP/2**

---

## Security Best Practices

1. **Use HTTPS in Production**
2. **Implement Rate Limiting**
3. **Sanitize User Inputs**
4. **Use Environment Variables for Secrets**
5. **Regular Security Updates**
6. **Implement CORS Properly**
7. **Use Strong Authentication**
8. **Enable Security Headers**

```python
# Security headers in FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
)
```

---

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -U username -d ephemeral > backup_$(date +%Y%m%d).sql

# Restore
psql -U username -d ephemeral < backup_20240101.sql
```

### Application State Backup

```bash
# Backup Docker volumes
docker run --rm -v ephemeral_data:/data -v $(pwd):/backup alpine tar czf /backup/data_backup.tar.gz /data

# Restore
docker run --rm -v ephemeral_data:/data -v $(pwd):/backup alpine tar xzf /backup/data_backup.tar.gz -C /
```

---

## Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  backend:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 2G
```

### Load Balancing

```nginx
# Nginx load balancer
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

---

## Support & Maintenance

### Regular Maintenance Tasks

1. **Weekly**: Review logs for errors
2. **Monthly**: Update dependencies
3. **Quarterly**: Security audit
4. **Annually**: Performance review

### Monitoring Checklist

- [ ] Application uptime
- [ ] Response times
- [ ] Error rates
- [ ] Memory usage
- [ ] CPU usage
- [ ] Disk space
- [ ] Database performance
- [ ] WebSocket connections

---

## Made with Bob for IBM AI Builders Challenge 2024