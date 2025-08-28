# Python AI Service Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpoppler-cpp-dev \
    poppler-utils \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r arxos && useradd -r -g arxos arxos

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install gRPC tools
RUN pip install --no-cache-dir \
    grpcio==1.59.0 \
    grpcio-tools==1.59.0 \
    grpcio-reflection==1.59.0

# Copy proto files and generate Python code
COPY ../proto /app/proto
RUN python -m grpc_tools.protoc \
    -I/app/proto \
    --python_out=/app \
    --grpc_python_out=/app \
    /app/proto/ingestion/ingestion.proto

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/models /app/temp /app/logs && \
    chown -R arxos:arxos /app

# Download pre-trained models (optional, for production)
# RUN python download_models.py

USER arxos

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    GRPC_PORT=50051 \
    LOG_LEVEL=INFO

# Expose gRPC port
EXPOSE 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import grpc; channel = grpc.insecure_channel('localhost:50051'); grpc.channel_ready_future(channel).result(timeout=5)"

# Run the gRPC server
CMD ["python", "grpc_server.py"]