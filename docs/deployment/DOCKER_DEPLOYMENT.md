# Motadata Docker Deployment Guide for FaaS Services

## Overview

This guide explains how to deploy FaaS services using Docker containers.

## Prerequisites

- Docker installed
- Docker Compose (optional, for multi-service deployment)
- PostgreSQL database
- Redis (optional, for caching)

## Service Dockerfile

### Generic Service Dockerfile

```dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY .env .env

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run service
# Example: Agent Service
CMD ["uvicorn", "src.faas.services.agent_service.service:app", "--host", "0.0.0.0", "--port", "8083"]

# Example: Prompt Generator Service
# CMD ["uvicorn", "src.faas.services.prompt_generator_service.service:app", "--host", "0.0.0.0", "--port", "8087"]

# Example: LLMOps Service
# CMD ["uvicorn", "src.faas.services.llmops_service.service:app", "--host", "0.0.0.0", "--port", "8088"]
```

## Building Docker Images

### Build Individual Service

```bash
# Build Agent Service
docker build -f Dockerfile.agent -t motadata/agent-service:latest .

# Build RAG Service
docker build -f Dockerfile.rag -t motadata/rag-service:latest .

# Build Gateway Service
docker build -f Dockerfile.gateway -t motadata/gateway-service:latest .
```

## Docker Compose Deployment

### docker-compose.yml

```yaml
version: '3.8'

services:
  # Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: motadata_ai
      POSTGRES_USER: motadata
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U motadata"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Gateway Service
  gateway-service:
    build:
      context: .
      dockerfile: Dockerfile.gateway
    environment:
      SERVICE_NAME: gateway-service
      SERVICE_PORT: 8080
      DATABASE_URL: postgresql://motadata:password@postgres:5432/motadata_ai
      REDIS_URL: redis://redis:6379
      ENABLE_NATS: "false"
      ENABLE_OTEL: "false"
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Cache Service
  cache-service:
    build:
      context: .
      dockerfile: Dockerfile.cache
    environment:
      SERVICE_NAME: cache-service
      SERVICE_PORT: 8081
      REDIS_URL: redis://redis:6379
    ports:
      - "8081:8081"
    depends_on:
      redis:
        condition: service_healthy

  # RAG Service
  rag-service:
    build:
      context: .
      dockerfile: Dockerfile.rag
    environment:
      SERVICE_NAME: rag-service
      SERVICE_PORT: 8082
      DATABASE_URL: postgresql://motadata:password@postgres:5432/motadata_ai
      GATEWAY_SERVICE_URL: http://gateway-service:8080
      CACHE_SERVICE_URL: http://cache-service:8081
    ports:
      - "8082:8082"
    depends_on:
      postgres:
        condition: service_healthy
      gateway-service:
        condition: service_healthy
      cache-service:
        condition: service_healthy

  # Agent Service
  agent-service:
    build:
      context: .
      dockerfile: Dockerfile.agent
    environment:
      SERVICE_NAME: agent-service
      SERVICE_PORT: 8083
      DATABASE_URL: postgresql://motadata:password@postgres:5432/motadata_ai
      GATEWAY_SERVICE_URL: http://gateway-service:8080
      CACHE_SERVICE_URL: http://cache-service:8081
      RAG_SERVICE_URL: http://rag-service:8082
    ports:
      - "8083:8083"
    depends_on:
      postgres:
        condition: service_healthy
      gateway-service:
        condition: service_healthy
      cache-service:
        condition: service_healthy
      rag-service:
        condition: service_healthy

volumes:
  postgres_data:
```

## Running Services

### Start All Services

```bash
docker-compose up -d
```

### Start Specific Service

```bash
docker-compose up -d agent-service
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f agent-service
```

### Stop Services

```bash
docker-compose down
```

## Service URLs

After deployment, services are available at:

- Gateway Service: `http://localhost:8080`
- Cache Service: `http://localhost:8081`
- RAG Service: `http://localhost:8082`
- Agent Service: `http://localhost:8083`

## Health Checks

All services expose health check endpoints:

```bash
curl http://localhost:8080/health  # Gateway Service
curl http://localhost:8081/health  # Cache Service
curl http://localhost:8082/health  # RAG Service
curl http://localhost:8083/health  # Agent Service
```

## Environment Variables

Each service can be configured via environment variables:

```bash
# Service Identity
SERVICE_NAME=agent-service
SERVICE_VERSION=1.0.0
SERVICE_PORT=8080

# Dependencies
GATEWAY_SERVICE_URL=http://gateway-service:8080
CACHE_SERVICE_URL=http://cache-service:8081
RAG_SERVICE_URL=http://rag-service:8082

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/db
REDIS_URL=redis://redis:6379

# Integrations
ENABLE_NATS=true
NATS_URL=nats://nats:4222
ENABLE_OTEL=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

## Production Considerations

1. **Use Docker Secrets** for sensitive data (API keys, passwords)
2. **Configure Resource Limits** (CPU, memory)
3. **Set up Logging** (centralized logging with ELK or similar)
4. **Configure Health Checks** (for orchestration)
5. **Use Docker Networks** (isolate services)
6. **Enable TLS** (for production deployments)

