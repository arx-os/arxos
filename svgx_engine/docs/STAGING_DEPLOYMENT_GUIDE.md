# SVGX Engine - Staging Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the SVGX Engine to a staging environment with full monitoring, alerting, and validation capabilities.

## Prerequisites

### Required Tools
- Docker (v20.10+)
- Kubernetes cluster (v1.24+)
- kubectl (configured for your cluster)
- Python 3.8+ (for validation scripts)

### Required Permissions
- Cluster admin or namespace admin permissions
- Docker registry access
- Persistent volume provisioning

## Architecture

### Components
1. **SVGX Engine Application**
   - FastAPI application with 10 endpoints
   - Performance monitoring and metrics
   - Security hardening and rate limiting
   - Health checks and readiness probes

2. **Monitoring Stack**
   - Prometheus for metrics collection
   - Grafana for visualization
   - AlertManager for alerting
   - Custom dashboards with CTO performance targets

3. **Infrastructure**
   - Kubernetes deployment with 2 replicas
   - Horizontal Pod Autoscaler
   - Persistent storage for cache and logs
   - SSL/TLS termination

## Deployment Steps

### Step 1: Environment Setup

```bash
# Set environment variables
export SVGX_NAMESPACE=svgx-engine-staging
export SVGX_IMAGE_NAME=svgx-engine
export SVGX_IMAGE_TAG=staging
export SVGX_REGISTRY=localhost:5000

# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

### Step 2: Build and Push Docker Image

```bash
# Build the image
docker build -t svgx-engine:staging .

# Tag for registry
docker tag svgx-engine:staging localhost:5000/svgx-engine:staging

# Push to registry
docker push localhost:5000/svgx-engine:staging
```

### Step 3: Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace svgx-engine-staging

# Apply staging deployment
kubectl apply -f k8s/staging-deployment.yaml

# Apply monitoring stack
kubectl apply -f k8s/monitoring.yaml

# Verify deployment
kubectl get pods -n svgx-engine-staging
kubectl get services -n svgx-engine-staging
```

### Step 4: Automated Deployment

```bash
# Run automated deployment script
python scripts/deploy_staging.py

# The script will:
# 1. Build Docker image
# 2. Push to registry
# 3. Deploy to Kubernetes
# 4. Wait for readiness
# 5. Run validation tests
```

## Validation and Testing

### Health Check
```bash
# Check application health
curl -H "Authorization: Bearer staging-api-key-test" \
     http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0-staging",
  "performance": {
    "response_time_ms": 2.5,
    "memory_usage_mb": 45.2,
    "cpu_usage_percent": 12.3
  }
}
```

### Performance Testing
```bash
# Run comprehensive validation
python scripts/staging_validation.py

# This will test:
# - CTO performance targets (<16ms UI, <32ms redraw, <100ms physics)
# - Load testing with concurrent users
# - Security validation
# - Error rate monitoring
```

### Load Testing
```bash
# Manual load testing
ab -n 1000 -c 10 -H "Authorization: Bearer staging-api-key-test" \
   http://localhost:8000/health

# Expected results:
# - Response time < 16ms (CTO target)
# - Success rate > 99.5%
# - No 5xx errors
```

## Monitoring and Alerting

### Access Monitoring Stack

```bash
# Port forward for local access
kubectl port-forward -n svgx-engine-staging service/grafana 3000:3000
kubectl port-forward -n svgx-engine-staging service/prometheus 9090:9090
kubectl port-forward -n svgx-engine-staging service/alertmanager 9093:9093
```

### Grafana Dashboard
- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin123
- **Dashboard**: SVGX Engine - Staging Dashboard

### Key Metrics to Monitor

1. **Performance Targets (CTO Directives)**
   - Response Time: < 16ms (UI), < 32ms (redraw), < 100ms (physics)
   - Memory Usage: < 1GB
   - CPU Usage: < 80%

2. **Business Metrics**
   - Request Rate: requests/second
   - Error Rate: < 1%
   - Success Rate: > 99.5%
   - Active Connections

3. **Infrastructure Metrics**
   - Pod Status: Running
   - Resource Usage: CPU/Memory
   - Network I/O
   - Disk I/O

### Alerting Rules

The monitoring stack includes the following alerts:

1. **HighResponseTime** (Warning)
   - Trigger: P95 response time > 16ms
   - Duration: 2 minutes
   - Action: Investigate performance issues

2. **HighErrorRate** (Critical)
   - Trigger: Error rate > 1%
   - Duration: 1 minute
   - Action: Immediate investigation

3. **ServiceDown** (Critical)
   - Trigger: Service unavailable
   - Duration: 30 seconds
   - Action: Immediate response

4. **HighMemoryUsage** (Warning)
   - Trigger: Memory > 800MB
   - Duration: 5 minutes
   - Action: Scale up or optimize

5. **HighCPUUsage** (Warning)
   - Trigger: CPU > 80%
   - Duration: 5 minutes
   - Action: Scale up or optimize

## Troubleshooting

### Common Issues

#### 1. Pod Not Starting
```bash
# Check pod status
kubectl get pods -n svgx-engine-staging

# Check pod logs
kubectl logs -n svgx-engine-staging deployment/svgx-engine-staging

# Check events
kubectl get events -n svgx-engine-staging --sort-by='.lastTimestamp'
```

#### 2. Health Check Failing
```bash
# Check health endpoint directly
curl -v http://localhost:8000/health

# Check readiness probe
kubectl describe pod -n svgx-engine-staging -l app=svgx-engine-staging
```

#### 3. Performance Issues
```bash
# Check resource usage
kubectl top pods -n svgx-engine-staging

# Check metrics
curl http://localhost:8000/metrics

# Check Grafana dashboard for trends
```

#### 4. Monitoring Not Working
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check AlertManager
curl http://localhost:9093/api/v1/alerts

# Check Grafana datasources
```

### Rollback Procedures

#### Manual Rollback
```bash
# Delete current deployment
kubectl delete -f k8s/staging-deployment.yaml

# Apply previous version
kubectl apply -f k8s/staging-deployment-previous.yaml

# Verify rollback
kubectl get pods -n svgx-engine-staging
```

#### Automated Rollback
```bash
# The deployment script includes automatic rollback
python scripts/deploy_staging.py

# If validation fails, rollback occurs automatically
```

## Security Considerations

### Network Security
- All traffic encrypted with TLS
- Internal service communication within cluster
- External access through ingress with SSL termination

### Authentication
- API key authentication required
- Rate limiting enabled
- Input validation on all endpoints

### Monitoring Security
- Prometheus metrics exposed internally only
- Grafana access controlled
- AlertManager configured for secure notifications

## Performance Optimization

### CTO Performance Targets
1. **UI Response Time**: < 16ms
   - Optimized parsing and evaluation
   - Caching for repeated operations
   - Async processing for non-critical operations

2. **Redraw Time**: < 32ms
   - Efficient SVG rendering
   - Incremental updates
   - Optimized data structures

3. **Physics Simulation**: < 100ms
   - Batch processing for constraints
   - Deferred global solves
   - Tiered precision implementation

### Resource Optimization
- Memory limits: 2GB per pod
- CPU limits: 2000m per pod
- Horizontal scaling based on CPU/Memory usage
- Persistent storage for cache and logs

## Maintenance

### Regular Tasks
1. **Daily**
   - Check monitoring dashboards
   - Review alert history
   - Monitor resource usage

2. **Weekly**
   - Review performance metrics
   - Update monitoring rules
   - Clean up old logs

3. **Monthly**
   - Update dependencies
   - Review security patches
   - Performance optimization review

### Backup and Recovery
```bash
# Backup configuration
kubectl get configmap -n svgx-engine-staging -o yaml > backup-config.yaml
kubectl get secret -n svgx-engine-staging -o yaml > backup-secrets.yaml

# Backup persistent data
kubectl exec -n svgx-engine-staging deployment/svgx-engine-staging -- tar czf /tmp/backup.tar.gz /app/svgx_cache
kubectl cp svgx-engine-staging/svgx-engine-staging-xxx:/tmp/backup.tar.gz ./backup.tar.gz
```

## Success Criteria

### Deployment Success
- [ ] All pods running and healthy
- [ ] Health checks passing
- [ ] Monitoring stack operational
- [ ] Validation tests passing

### Performance Success
- [ ] Response time < 16ms (UI)
- [ ] Response time < 32ms (redraw)
- [ ] Response time < 100ms (physics)
- [ ] Error rate < 1%
- [ ] Success rate > 99.5%

### Security Success
- [ ] Authentication working
- [ ] Rate limiting active
- [ ] Input validation effective
- [ ] No security vulnerabilities

### Monitoring Success
- [ ] Metrics collection working
- [ ] Alerts configured and tested
- [ ] Dashboards operational
- [ ] Log aggregation functional

## Next Steps

After successful staging deployment:

1. **Production Deployment**
   - Deploy to production environment
   - Configure production monitoring
   - Set up production alerting

2. **Phase 5 Implementation**
   - Begin advanced simulation engine
   - Implement interactive capabilities
   - Develop ArxIDE integration
   - Create CAD-parity features

3. **Specialized Services**
   - Implement NLP CLI integration
   - Create CMMS maintenance hooks
   - Develop enhanced spatial reasoning
   - Add distributed processing

4. **Continuous Improvement**
   - Monitor performance trends
   - Optimize based on usage patterns
   - Implement user feedback
   - Scale based on demand

## Support

For issues or questions:
- Check monitoring dashboards first
- Review logs for error details
- Consult troubleshooting section
- Contact engineering team

---

**Document Version**: 1.0
**Last Updated**: 2024
**Next Review**: Monthly
