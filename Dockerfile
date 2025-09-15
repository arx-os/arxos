# Multi-stage build for ArxOS
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev sqlite-dev git

# Set working directory
WORKDIR /build

# Copy go mod files
COPY go.mod go.sum go.work ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build all binaries
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o arx ./cmd/arx || true
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o arxd ./cmd/arxd || true
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o arxos-server ./cmd/arxos-server || true

# Final stage
FROM alpine:latest

# Install runtime dependencies
RUN apk --no-cache add ca-certificates sqlite-libs

# Create app user
RUN addgroup -g 1000 arxos && \
    adduser -D -u 1000 -G arxos arxos

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/migrations && \
    chown -R arxos:arxos /app

WORKDIR /app

# Copy binaries from builder
COPY --from=builder /build/arx* /app/
COPY --from=builder /build/migrations /app/migrations

# Copy configuration files
COPY --chown=arxos:arxos .env.example /app/.env.example

# Switch to non-root user
USER arxos

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/app/arxos-server", "--health-check"] || exit 1

# Default command
CMD ["/app/arxos-server"]