# Deployment Guide

This document outlines guidelines to deploy **EmotionVision AI** to a production cloud server (such as AWS, GCP, or Azure) using Docker and Nginx.

---

## 1. Production Dockerization

We can package the application into a single container or separate backend and frontend containers. The recommended approach for cloud deployments is a **multi-container setup** orchestrated via Docker Compose.

### Dockerfile (Backend & API)
Save the following as `Dockerfile` in the root or `backend/` directory:
```dockerfile
# Multi-stage build for FastAPI backend
FROM python:3.10-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.10-slim as runner
WORKDIR /app

# Install system dependencies for OpenCV & MediaPipe
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 2. Nginx Reverse Proxy Config

To run the application behind an Nginx reverse proxy, configure Nginx to route WebSockets properly. Save the following inside `/etc/nginx/sites-available/default`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend React Static Files
    location / {
        root /var/www/emotionvision/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Backend REST API
    location /api {
        proxy_pass http://127.0.0.1:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend WebSockets Stream
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 86400; # 24 hours socket timeout
    }
}
```

---

## 3. Environment Variable Configuration

Create a `.env` file in the production directory:
```env
DEBUG=False
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=["https://yourdomain.com"]
```
This restricts cross-origin request policies to your specific domains, protecting your local loopback.
