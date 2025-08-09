# SVGX Engine - Production Dockerfile
# Multi-stage build for security and performance

# --- Build Stage ---
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --prefix=/install -r requirements.txt

# --- Runtime Stage ---
FROM python:3.11-slim
WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /install /usr/local

# Copy SVGX Engine source
COPY . .

# Create non-root user
RUN useradd -m svgxuser
USER svgxuser

# Expose default port
EXPOSE 8080

# Set environment variables (can be overridden at runtime)
ENV SVGX_ENV=production \
    PYTHONUNBUFFERED=1

# Healthcheck (assumes FastAPI/Uvicorn)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:8080/health || exit 1

# Start the SVGX Engine (assumes FastAPI/Uvicorn app: app.py or main.py)
CMD ["python", "-m", "svgx_engine.app"]
