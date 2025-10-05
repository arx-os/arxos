# ArxOS Dockerfile
# Multi-stage build for optimized production image with BuildKit cache optimization

# Build arguments for version injection
ARG VERSION=unknown
ARG COMMIT=unknown
ARG BUILD_TIME=""

# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /app

# Copy go mod files first for better layer caching
COPY go.mod go.sum ./

# Download dependencies with cache mount
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download && go mod verify

# Copy only necessary source directories (optimizes layer caching)
COPY cmd/ cmd/
COPY internal/ internal/
COPY pkg/ pkg/

# Build the application with version information and cache mounts
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux go install \
    -a -installsuffix cgo \
    -ldflags="-s -w -X github.com/arx-os/arxos/cmd/arx.Version=${VERSION} -X github.com/arx-os/arxos/cmd/arx.Commit=${COMMIT} -X github.com/arx-os/arxos/cmd/arx.BuildTime=${BUILD_TIME}" \
    ./cmd/arx

# Production stage
FROM alpine:3.19

# Install runtime dependencies including spatial computing tools
RUN apk add --no-cache \
    ca-certificates \
    tzdata \
    curl \
    postgresql-client \
    # ArxOS spatial computing dependencies
    gdal \
    geos \
    proj \
    spatialite \
    sqlite \
    # Additional utilities for spatial data processing
    gdal-dev \
    geos-dev \
    proj-dev \
    sqlite-dev

# Create non-root user
RUN adduser -D -s /bin/sh arxos

# Set working directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /go/bin/arx .

# Copy configuration templates
COPY configs/ ./configs/

# Copy scripts
COPY scripts/ ./scripts/

# Set permissions and security hardening
RUN chmod +x ./arx && \
    # Create application directories with proper ownership
    mkdir -p /app/data /app/logs /app/cache /tmp/arxos && \
    chown -R arxos:arxos /app && \
    chown -R arxos:arxos /tmp/arxos && \
    # Set secure permissions on config directory
    chmod -R 755 /app/configs && \
    chmod -R 755 /app/scripts

# Add security labels
LABEL org.opencontainers.image.title="ArxOS" \
      org.opencontainers.image.description="ArxOS - The Building Operating System" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${COMMIT}" \
      org.opencontainers.image.created="${BUILD_TIME}" \
      security.scan.enabled="true" \
      security.non-root=true

# Switch to non-root user
USER arxos

# Set working directory permissions
WORKDIR /app

# Expose port
EXPOSE 8080

# Add volume mount points for persistent data
VOLUME ["/app/data", "/app/logs", "/app/cache"]

# Health check with comprehensive monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8080/health && \
         curl -f http://localhost:8080/api/v1/status || exit 1

# Default command
CMD ["./arx", "serve"]
