# Arxos Kubernetes Deployment

This directory contains all Kubernetes manifests for the Arxos platform deployment.

## Directory Structure

```
k8s/
├── namespaces.yaml              # Namespace definitions
├── svgx-engine.yaml            # SVGX Engine service deployment
├── export-service.yaml          # Export service deployment
├── ingress.yaml                 # Ingress configuration
├── monitoring.yaml              # Monitoring and alerting configuration
└── environments/                # Environment-specific configurations
    ├── production.yaml          # Production environment (export service)
    ├── production-svgx.yaml     # Production environment (SVGX engine)
    ├── staging.yaml             # Staging environment
    └── dev.yaml                 # Development environment
```

## Services

### SVGX Engine
- **Namespace**: `arxos` (default), `arxos-production` (production)
- **Image**: `ghcr.io/arxos/svgx-engine:latest`
- **Port**: 8000
- **Health Check**: `/health/`
- **Metrics**: `/metrics/prometheus`

### Export Service
- **Namespace**: `arxos` (default), `arxos-production` (production)
- **Image**: `arxos/export-service:latest`
- **Port**: 8000
- **Health Check**: `/healthz`
- **Metrics**: `/metrics`

## Namespaces

- `arxos`: Default namespace for all services
- `arxos-dev`: Development environment
- `arxos-staging`: Staging environment
- `arxos-production`: Production environment

## Deployment

### Prerequisites

1. Kubernetes cluster with:
   - Nginx Ingress Controller
   - Prometheus Operator (for monitoring)
   - Cert-Manager (for SSL certificates)

2. Required secrets:
   - `arxos-redis-secret`
   - `arxos-database-secret`
   - `arxos-jwt-secret`

### Quick Start

1. **Deploy namespaces**:
   ```bash
   kubectl apply -f namespaces.yaml
   ```

2. **Deploy core services**:
   ```bash
   kubectl apply -f svgx-engine.yaml
   kubectl apply -f export-service.yaml
   ```

3. **Deploy ingress and monitoring**:
   ```bash
   kubectl apply -f ingress.yaml
   kubectl apply -f monitoring.yaml
   ```

4. **Deploy environment-specific configurations**:
   ```bash
   # For production
   kubectl apply -f environments/production.yaml
   kubectl apply -f environments/production-svgx.yaml
   
   # For staging
   kubectl apply -f environments/staging.yaml
   
   # For development
   kubectl apply -f environments/dev.yaml
   ```

## Configuration

### Environment Variables

Both services use the following environment variables:
- `REDIS_URL`: Redis connection string
- `POSTGRES_URL`: PostgreSQL connection string
- `JWT_SECRET`: JWT signing secret
- `ENVIRONMENT`: Environment name (production, staging, dev)
- `LOG_LEVEL`: Logging level (INFO, WARNING, ERROR)

### Resource Limits

**SVGX Engine**:
- Requests: 512Mi memory, 250m CPU
- Limits: 1Gi memory, 500m CPU
- Production: 1Gi memory, 500m CPU requests, 2Gi memory, 1000m CPU limits

**Export Service**:
- Requests: 512Mi memory, 250m CPU
- Limits: 2Gi memory, 1000m CPU

### Scaling

Both services use HorizontalPodAutoscaler:
- **Default**: 3-10 replicas
- **Production**: 5-20 replicas
- **CPU target**: 70% utilization
- **Memory target**: 80% utilization

## Monitoring

### Prometheus Integration

Both services expose metrics endpoints:
- SVGX Engine: `/metrics/prometheus`
- Export Service: `/metrics`

### Alerts

The monitoring configuration includes alerts for:
- High error rates
- High response times
- High CPU/memory usage
- Pod down status
- WebSocket connection limits
- Rate limit hits
- Disk usage
- Network errors
- Frequent restarts

## Security

### Pod Security

All pods run with:
- Non-root user (UID 1000)
- Read-only root filesystem
- Dropped capabilities
- Security context restrictions

### Network Security

- SSL/TLS termination at ingress
- Rate limiting configured
- WebSocket support with proper headers
- Health check endpoints

## Troubleshooting

### Common Issues

1. **Pod not starting**:
   - Check secrets exist: `kubectl get secrets -n arxos`
   - Check PVC status: `kubectl get pvc -n arxos`
   - Check events: `kubectl describe pod <pod-name> -n arxos`

2. **Service not accessible**:
   - Check service endpoints: `kubectl get endpoints -n arxos`
   - Check ingress status: `kubectl get ingress -n arxos`
   - Check DNS resolution

3. **High resource usage**:
   - Check HPA status: `kubectl get hpa -n arxos`
   - Check pod metrics: `kubectl top pods -n arxos`

### Logs

View service logs:
```bash
# SVGX Engine
kubectl logs -f deployment/svgx-engine -n arxos

# Export Service
kubectl logs -f deployment/arxos-export-service -n arxos
```

### Metrics

Access metrics directly:
```bash
# SVGX Engine metrics
kubectl port-forward svc/svgx-engine-service 8000:80 -n arxos
curl http://localhost:8000/metrics/prometheus

# Export Service metrics
kubectl port-forward svc/arxos-export-service 8000:8000 -n arxos
curl http://localhost:8000/metrics
```

## Maintenance

### Updates

1. **Image updates**: Update image tags in deployment files
2. **Configuration changes**: Update ConfigMaps and redeploy
3. **Resource adjustments**: Update resource limits and HPA settings

### Backup

- Database backups should be configured separately
- PVC data is persistent but should be backed up
- Configuration is stored in ConfigMaps and can be exported

### Rollback

Use Kubernetes rollback:
```bash
kubectl rollout undo deployment/svgx-engine -n arxos
kubectl rollout undo deployment/arxos-export-service -n arxos
``` 