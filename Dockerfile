# Multi-stage build for ArxOS
FROM golang:1.21-alpine AS builder

# Install build dependencies (minimal set for pure Go build)
RUN apk add --no-cache git ca-certificates tzdata

# Set working directory
WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build single binary with pure Go (no CGO)
# Using PostGIS for spatial operations
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -a -installsuffix cgo \
    -ldflags='-w -s -extldflags "-static"' \
    -o arx ./cmd/arx

# Final stage - minimal container for pure Go binary
FROM alpine:latest

# Install runtime dependencies (minimal for static binary)
RUN apk --no-cache add ca-certificates tzdata

# Create app user
RUN addgroup -g 1000 arxos && \
    adduser -D -u 1000 -G arxos arxos

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/migrations && \
    chown -R arxos:arxos /app

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/arx /app/arx

# Copy timezone data and certificates for proper time handling and HTTPS
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy configuration files
COPY --chown=arxos:arxos .env.example /app/.env.example

# Switch to non-root user
USER arxos

# Expose ports
EXPOSE 8080 9090

# Health check for ArxOS API server
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["/app/arx", "health"] || exit 1

# Default command - run server mode
CMD ["/app/arx", "serve"]