# Build stage
FROM golang:1.21-alpine AS builder

# Install build dependencies
RUN apk add --no-cache git make gcc musl-dev

WORKDIR /build

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Generate proto files
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@latest
RUN go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest

# Build the application
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o arxos ./cmd/main.go

# Runtime stage
FROM alpine:3.18

# Install runtime dependencies
RUN apk add --no-cache ca-certificates tzdata

# Create non-root user
RUN addgroup -g 1001 -S arxos && \
    adduser -u 1001 -S arxos -G arxos

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/arxos /app/arxos

# Copy configuration files
COPY --from=builder /build/config /app/config

# Create necessary directories
RUN mkdir -p /tmp/arxos /app/data && \
    chown -R arxos:arxos /app /tmp/arxos

USER arxos

# Expose ports
EXPOSE 8080 8081 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["/app/arxos", "health"]

# Run the application
ENTRYPOINT ["/app/arxos"]
CMD ["serve"]