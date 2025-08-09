# SVGX Engine - Production Deployment Guide

## 1. Docker Deployment

- Build the Docker image:
  ```sh
  docker build -t svgx-engine:latest .
  ```
- Run the container:
  ```sh
  docker run -d -p 8080:8080 --env SVGX_ENV=production svgx-engine:latest
  ```
- Environment variables:
  - `SVGX_ENV`: Set to `production`, `staging`, or `development`.
  - `PYTHONUNBUFFERED`: Set to `1` for real-time logs.

## 2. Kubernetes Deployment

- Example `deployment.yaml`:
  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: svgx-engine
  spec:
    replicas: 2
    selector:
      matchLabels:
        app: svgx-engine
    template:
      metadata:
        labels:
          app: svgx-engine
      spec:
        containers:
        - name: svgx-engine
          image: svgx-engine:latest
          ports:
          - containerPort: 8080
          env:
          - name: SVGX_ENV
            value: "production"
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 30
  ```
- Example `service.yaml`:
  ```yaml
  apiVersion: v1
  kind: Service
  metadata:
    name: svgx-engine
  spec:
    type: ClusterIP
    selector:
      app: svgx-engine
    ports:
      - protocol: TCP
        port: 8080
        targetPort: 8080
  ```

## 3. Blue-Green Deployment

- Deploy new version alongside current version.
- Switch traffic to new deployment after health checks pass.
- Roll back by switching traffic back if issues are detected.

## 4. Health Checks

- `/health` endpoint should return 200 OK if service is healthy.
- Used by Docker and Kubernetes for liveness/readiness probes.

## 5. Monitoring & Logging

- Integrate with Prometheus, Grafana, or OpenTelemetry for metrics.
- Use structured logging (JSON or key-value pairs).
- Set up alerting for error rates, latency, and resource usage.

## 6. Rollback Procedures

- Use Kubernetes `rollout undo` to revert to previous deployment:
  ```sh
  kubectl rollout undo deployment/svgx-engine
  ```
- For Docker Compose, restart previous container version.

## 7. Backup & Disaster Recovery

- Regularly back up persistent data (if any).
- Store backups in secure, offsite location.
- Document recovery steps and test regularly.

## 8. Troubleshooting

- Check logs with `docker logs` or `kubectl logs`.
- Verify health endpoints and resource usage.
- Use monitoring dashboards for real-time insights.

---

For further details, see CTO directives and Phase 5 implementation roadmap.
