# Production-grade Dockerfile for Arxos Export Service
# Multi-stage build for optimized production image

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY arx_svg_parser/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /tmp/requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    ARXOS_ENVIRONMENT="production"

# Create non-root user for security
RUN groupadd -r arxos && useradd -r -g arxos arxos

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create application directory
WORKDIR /app

# Copy application code
COPY arx_svg_parser/ /app/arx_svg_parser/
COPY arx_svg_parser/scripts/ /app/scripts/
COPY arx_svg_parser/cli_commands/ /app/cli_commands/

# Create necessary directories
RUN mkdir -p /app/logs /app/exports /app/config /app/data && \
    chown -R arxos:arxos /app

# Copy configuration files
COPY arx-infra/config/export-service.yaml /app/config/
COPY arx-infra/config/logging.yaml /app/config/

# Create health check script
RUN echo '#!/bin/bash\n\
curl -f http://localhost:8000/healthz || exit 1' > /app/healthcheck.sh && \
    chmod +x /app/healthcheck.sh

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Wait for database if needed\n\
if [ -n "$DATABASE_URL" ]; then\n\
    echo "Waiting for database..."\n\
    python -c "\n\
import time\n\
import psycopg2\n\
from urllib.parse import urlparse\n\
\n\
parsed = urlparse(\"$DATABASE_URL\")\n\
while True:\n\
    try:\n\
        conn = psycopg2.connect(\n\
            host=parsed.hostname,\n\
            port=parsed.port or 5432,\n\
            database=parsed.path[1:],\n\
            user=parsed.username,\n\
            password=parsed.password\n\
        )\n\
        conn.close()\n\
        break\n\
    except Exception:\n\
        time.sleep(1)\n\
"\n\
fi\n\
\n\
# Run database migrations\n\
if [ -n "$RUN_MIGRATIONS" ]; then\n\
    echo "Running database migrations..."\n\
    alembic upgrade head\n\
fi\n\
\n\
# Start the application\n\
exec gunicorn \\\n\
    --bind 0.0.0.0:8000 \\\n\
    --workers ${WORKERS:-4} \\\n\
    --worker-class uvicorn.workers.UvicornWorker \\\n\
    --timeout ${TIMEOUT:-120} \\\n\
    --keep-alive 2 \\\n\
    --max-requests 1000 \\\n\
    --max-requests-jitter 100 \\\n\
    --access-logfile - \\\n\
    --error-logfile - \\\n\
    --log-level ${LOG_LEVEL:-info} \\\n\
    arx_svg_parser.api.main:app\n\
' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Switch to non-root user
USER arxos

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/healthcheck.sh

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "arx_svg_parser.api.main:app"] 