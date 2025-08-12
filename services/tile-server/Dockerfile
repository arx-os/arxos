# Dockerfile for Fractal ArxObject Tile Server
FROM golang:1.21-alpine AS builder

# Install dependencies
RUN apk add --no-cache git gcc musl-dev

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build the tile server
RUN CGO_ENABLED=1 GOOS=linux go build -a -installsuffix cgo -o tile-server ./cmd/server

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/tile-server .

# Expose port
EXPOSE 8080

# Run the server
CMD ["./tile-server"]