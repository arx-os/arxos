# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /build

# Copy go mod file
COPY go.mod ./
RUN go mod download

# Copy source code
COPY . .

# Build the binary
RUN CGO_ENABLED=0 GOOS=linux go build -o arxos-api ./core/backend/main.go

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /app

# Copy binary from builder
COPY --from=builder /build/arxos-api .

# Copy static files
COPY --from=builder /build/frontend/web ./static

EXPOSE 8080

CMD ["./arxos-api"]