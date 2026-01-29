# Motadata Kubernetes Deployment Guide for FaaS Services

## Overview

This guide explains how to deploy FaaS services on Kubernetes.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- PostgreSQL database (can be deployed separately)
- Redis (can be deployed separately)

## Service Deployment

### Agent Service Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-service
  labels:
    app: agent-service
    component: ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agent-service
  template:
    metadata:
      labels:
        app: agent-service
    spec:
      containers:
      - name: agent-service
        image: motadata/agent-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: SERVICE_NAME
          value: "agent-service"
        - name: SERVICE_PORT
          value: "8080"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: GATEWAY_SERVICE_URL
          value: "http://gateway-service:8080"
        - name: CACHE_SERVICE_URL
          value: "http://cache-service:8081"
        - name: RAG_SERVICE_URL
          value: "http://rag-service:8082"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: agent-service
spec:
  selector:
    app: agent-service
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

### RAG Service Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-service
  labels:
    app: rag-service
    component: ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-service
  template:
    metadata:
      labels:
        app: rag-service
    spec:
      containers:
      - name: rag-service
        image: motadata/rag-service:latest
        ports:
        - containerPort: 8082
        env:
        - name: SERVICE_NAME
          value: "rag-service"
        - name: SERVICE_PORT
          value: "8082"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-credentials
              key: url
        - name: GATEWAY_SERVICE_URL
          value: "http://gateway-service:8080"
        - name: CACHE_SERVICE_URL
          value: "http://cache-service:8081"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8082
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: rag-service
spec:
  selector:
    app: rag-service
  ports:
  - port: 8082
    targetPort: 8082
  type: ClusterIP
```

### Gateway Service Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway-service
  labels:
    app: gateway-service
    component: ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gateway-service
  template:
    metadata:
      labels:
        app: gateway-service
    spec:
      containers:
      - name: gateway-service
        image: motadata/gateway-service:latest
        ports:
        - containerPort: 8080
        env:
        - name: SERVICE_NAME
          value: "gateway-service"
        - name: SERVICE_PORT
          value: "8080"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-api-keys
              key: openai
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: gateway-service
spec:
  selector:
    app: gateway-service
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

## Ingress Configuration

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-services-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.motadata.com
    secretName: ai-services-tls
  rules:
  - host: api.motadata.com
    http:
      paths:
      - path: /api/v1/agents
        pathType: Prefix
        backend:
          service:
            name: agent-service
            port:
              number: 8080
      - path: /api/v1/rag
        pathType: Prefix
        backend:
          service:
            name: rag-service
            port:
              number: 8082
      - path: /api/v1/gateway
        pathType: Prefix
        backend:
          service:
            name: gateway-service
            port:
              number: 8080
```

## Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: database-credentials
type: Opaque
stringData:
  url: postgresql://user:password@postgres-service:5432/motadata_ai

---
apiVersion: v1
kind: Secret
metadata:
  name: redis-credentials
type: Opaque
stringData:
  url: redis://redis-service:6379

---
apiVersion: v1
kind: Secret
metadata:
  name: llm-api-keys
type: Opaque
stringData:
  openai: sk-...
  anthropic: sk-ant-...
```

## Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: agent-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-service
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Deployment Commands

### Deploy All Services

```bash
# Apply deployments
kubectl apply -f k8s/deployments/

# Apply services
kubectl apply -f k8s/services/

# Apply ingress
kubectl apply -f k8s/ingress/

# Apply secrets
kubectl apply -f k8s/secrets/
```

### Check Status

```bash
# Check pods
kubectl get pods -l component=ai

# Check services
kubectl get services -l component=ai

# Check logs
kubectl logs -f deployment/agent-service
```

### Scale Services

```bash
# Scale agent service
kubectl scale deployment agent-service --replicas=5

# Scale RAG service
kubectl scale deployment rag-service --replicas=5
```

## Service Discovery

Services can discover each other using Kubernetes DNS:

- `gateway-service.default.svc.cluster.local:8080`
- `rag-service.default.svc.cluster.local:8082`
- `agent-service.default.svc.cluster.local:8083`

Or using service names within the same namespace:

- `http://gateway-service:8080`
- `http://rag-service:8082`
- `http://agent-service:8083`

## Monitoring

### Prometheus ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: agent-service-monitor
spec:
  selector:
    matchLabels:
      app: agent-service
  endpoints:
  - port: http
    path: /metrics
```

## Best Practices

1. **Use ConfigMaps** for non-sensitive configuration
2. **Use Secrets** for sensitive data (API keys, passwords)
3. **Set Resource Limits** to prevent resource exhaustion
4. **Configure Health Checks** (liveness and readiness probes)
5. **Use Horizontal Pod Autoscaler** for automatic scaling
6. **Enable Pod Disruption Budgets** for high availability
7. **Use Network Policies** for service isolation
8. **Configure Logging** (centralized logging with Fluentd/Fluent Bit)

