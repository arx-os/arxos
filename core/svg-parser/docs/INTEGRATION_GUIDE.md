# Arxos Integration Guide

## Table of Contents

1. [Overview](#overview)
2. [API Integration](#api-integration)
3. [Third-Party Integrations](#third-party-integrations)
4. [Development Workflows](#development-workflows)
5. [Testing & Validation](#testing--validation)
6. [Deployment Integration](#deployment-integration)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Arxos platform provides comprehensive integration capabilities for third-party systems, development workflows, and external services. This guide covers all integration patterns and best practices.

### Integration Types

- **API Integration**: RESTful API endpoints
- **Webhook Integration**: Real-time event notifications
- **File Integration**: Import/export file formats
- **Database Integration**: Direct database connections
- **Cloud Integration**: Cloud service providers
- **Mobile Integration**: Mobile app SDKs

---

## API Integration

### Authentication

#### 1. API Key Authentication

```python
import requests

# API key authentication
headers = {
    "Authorization": "Bearer your-api-key-here",
    "Content-Type": "application/json"
}

response = requests.get("https://api.arxos.com/api/v1/health", headers=headers)
```

#### 2. OAuth 2.0 Integration

```python
from services.oauth_client import OAuthClient

# Initialize OAuth client
oauth = OAuthClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    redirect_uri="https://your-app.com/callback"
)

# Get authorization URL
auth_url = oauth.get_authorization_url()

# Exchange code for token
token = oauth.exchange_code_for_token(authorization_code)

# Use token for API calls
headers = {"Authorization": f"Bearer {token.access_token}"}
```

### Core API Operations

#### 1. SVG Upload and Processing

```python
import requests

# Upload SVG file
with open("building_plan.svg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "https://api.arxos.com/api/v1/upload/svg",
        headers=headers,
        files=files
    )

svg_id = response.json()["svg_id"]

# Process SVG to BIM
bim_response = requests.post(
    "https://api.arxos.com/api/v1/assemble/bim",
    headers=headers,
    data={
        "svg_id": svg_id,
        "format": "json"
    }
)
```

#### 2. Export Operations

```python
# Create export job
export_job = requests.post(
    "https://api.arxos.com/api/v1/export/create-job",
    headers=headers,
    json={
        "building_id": "building_001",
        "format": "ifc-lite",
        "options": {
            "include_metadata": True,
            "compression": True
        }
    }
)

job_id = export_job.json()["job_id"]

# Monitor job status
while True:
    status_response = requests.get(
        f"https://api.arxos.com/api/v1/export/jobs/{job_id}",
        headers=headers
    )
    
    status = status_response.json()["status"]
    if status == "completed":
        break
    elif status == "failed":
        raise Exception("Export failed")
    
    time.sleep(5)

# Download exported file
download_response = requests.get(
    f"https://api.arxos.com/api/v1/export/download/{job_id}",
    headers=headers
)

with open("building.ifc", "wb") as f:
    f.write(download_response.content)
```

#### 3. Security Operations

```python
# Apply privacy controls
privacy_response = requests.post(
    "https://api.arxos.com/api/v1/security/privacy/controls",
    headers=headers,
    json={
        "data": {"building_info": "sensitive data"},
        "classification": "confidential"
    }
)

# Encrypt data
encrypt_response = requests.post(
    "https://api.arxos.com/api/v1/security/encryption/encrypt",
    headers=headers,
    json={
        "data": "sensitive data",
        "layer": "storage"
    }
)

# Check permissions
permission_response = requests.post(
    "https://api.arxos.com/api/v1/security/rbac/check-permission",
    headers=headers,
    json={
        "user_id": "user123",
        "resource": "building",
        "action": "read"
    }
)
```

### Webhook Integration

#### 1. Webhook Configuration

```python
# Register webhook
webhook_response = requests.post(
    "https://api.arxos.com/api/v1/webhooks/register",
    headers=headers,
    json={
        "url": "https://your-app.com/webhooks/arxos",
        "events": ["export.completed", "security.violation", "audit.event"],
        "secret": "your-webhook-secret"
    }
)
```

#### 2. Webhook Handler

```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)

@app.route("/webhooks/arxos", methods=["POST"])
def handle_webhook():
    # Verify webhook signature
    signature = request.headers.get("X-Arxos-Signature")
    payload = request.get_data()
    
    expected_signature = hmac.new(
        "your-webhook-secret".encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return "Unauthorized", 401
    
    # Process webhook event
    event = request.json
    
    if event["type"] == "export.completed":
        handle_export_completed(event)
    elif event["type"] == "security.violation":
        handle_security_violation(event)
    elif event["type"] == "audit.event":
        handle_audit_event(event)
    
    return "OK", 200

def handle_export_completed(event):
    print(f"Export completed: {event['data']['job_id']}")

def handle_security_violation(event):
    print(f"Security violation: {event['data']['violation_type']}")

def handle_audit_event(event):
    print(f"Audit event: {event['data']['event_type']}")
```

---

## Third-Party Integrations

### CAD Software Integration

#### 1. AutoCAD Integration

```python
from services.autocad_integration import AutoCADIntegration

autocad = AutoCADIntegration()

# Export to AutoCAD
autocad.export_to_autocad(
    building_data=building_data,
    output_path="building.dwg",
    options={
        "scale": 1.0,
        "units": "meters",
        "layers": True
    }
)

# Import from AutoCAD
building_data = autocad.import_from_autocad(
    file_path="building.dwg",
    options={
        "extract_metadata": True,
        "preserve_layers": True
    }
)
```

#### 2. Revit Integration

```python
from services.revit_integration import RevitIntegration

revit = RevitIntegration()

# Export to Revit
revit.export_to_revit(
    building_data=building_data,
    output_path="building.rvt",
    options={
        "family_creation": True,
        "parameter_mapping": True
    }
)

# Import from Revit
building_data = revit.import_from_revit(
    file_path="building.rvt",
    options={
        "extract_families": True,
        "preserve_parameters": True
    }
)
```

### BIM Software Integration

#### 1. IFC Integration

```python
from services.ifc_integration import IFCIntegration

ifc = IFCIntegration()

# Export to IFC
ifc.export_to_ifc(
    building_data=building_data,
    output_path="building.ifc",
    options={
        "schema_version": "IFC4",
        "include_properties": True,
        "spatial_structure": True
    }
)

# Import from IFC
building_data = ifc.import_from_ifc(
    file_path="building.ifc",
    options={
        "extract_properties": True,
        "preserve_spatial_structure": True
    }
)
```

#### 2. glTF Integration

```python
from services.gltf_integration import glTFIntegration

gltf = glTFIntegration()

# Export to glTF
gltf.export_to_gltf(
    building_data=building_data,
    output_path="building.gltf",
    options={
        "include_textures": True,
        "optimize_geometry": True,
        "animation": False
    }
)
```

### Cloud Service Integration

#### 1. AWS Integration

```python
from services.aws_integration import AWSIntegration

aws = AWSIntegration(
    access_key="your-access-key",
    secret_key="your-secret-key",
    region="us-east-1"
)

# Upload to S3
aws.upload_to_s3(
    file_path="building.ifc",
    bucket="arxos-buildings",
    key="buildings/building_001.ifc"
)

# Download from S3
aws.download_from_s3(
    bucket="arxos-buildings",
    key="buildings/building_001.ifc",
    local_path="building.ifc"
)
```

#### 2. Azure Integration

```python
from services.azure_integration import AzureIntegration

azure = AzureIntegration(
    connection_string="your-connection-string"
)

# Upload to Blob Storage
azure.upload_to_blob(
    file_path="building.ifc",
    container="buildings",
    blob_name="building_001.ifc"
)

# Download from Blob Storage
azure.download_from_blob(
    container="buildings",
    blob_name="building_001.ifc",
    local_path="building.ifc"
)
```

#### 3. Google Cloud Integration

```python
from services.gcp_integration import GCPIntegration

gcp = GCPIntegration(
    project_id="your-project-id",
    credentials_path="path/to/credentials.json"
)

# Upload to Cloud Storage
gcp.upload_to_storage(
    file_path="building.ifc",
    bucket="arxos-buildings",
    blob_name="buildings/building_001.ifc"
)

# Download from Cloud Storage
gcp.download_from_storage(
    bucket="arxos-buildings",
    blob_name="buildings/building_001.ifc",
    local_path="building.ifc"
)
```

### Database Integration

#### 1. PostgreSQL Integration

```python
from services.postgresql_integration import PostgreSQLIntegration

postgres = PostgreSQLIntegration(
    host="localhost",
    port=5432,
    database="arxos",
    username="user",
    password="password"
)

# Store building data
postgres.store_building_data(
    building_id="building_001",
    building_data=building_data,
    metadata={"version": "1.0", "created_by": "user123"}
)

# Retrieve building data
building_data = postgres.get_building_data("building_001")
```

#### 2. MongoDB Integration

```python
from services.mongodb_integration import MongoDBIntegration

mongo = MongoDBIntegration(
    connection_string="mongodb://localhost:27017/arxos"
)

# Store building data
mongo.store_building_data(
    building_id="building_001",
    building_data=building_data
)

# Query building data
buildings = mongo.query_buildings({
    "building_type": "commercial",
    "floors": {"$gte": 5}
})
```

### Mobile Integration

#### 1. iOS SDK

```swift
import ArxosSDK

// Initialize SDK
let arxos = ArxosSDK(apiKey: "your-api-key")

// Upload SVG
arxos.uploadSVG(filePath: "building.svg") { result in
    switch result {
    case .success(let svgId):
        print("Uploaded SVG with ID: \(svgId)")
    case .failure(let error):
        print("Upload failed: \(error)")
    }
}

// Export to BIM
arxos.exportToBIM(buildingId: "building_001", format: .ifc) { result in
    switch result {
    case .success(let filePath):
        print("Exported to: \(filePath)")
    case .failure(let error):
        print("Export failed: \(error)")
    }
}
```

#### 2. Android SDK

```kotlin
import com.arxos.sdk.ArxosSDK

// Initialize SDK
val arxos = ArxosSDK(apiKey = "your-api-key")

// Upload SVG
arxos.uploadSVG("building.svg") { result ->
    when (result) {
        is Result.Success -> {
            println("Uploaded SVG with ID: ${result.data}")
        }
        is Result.Failure -> {
            println("Upload failed: ${result.error}")
        }
    }
}

// Export to BIM
arxos.exportToBIM("building_001", ExportFormat.IFC) { result ->
    when (result) {
        is Result.Success -> {
            println("Exported to: ${result.data}")
        }
        is Result.Failure -> {
            println("Export failed: ${result.error}")
        }
    }
}
```

---

## Development Workflows

### CI/CD Integration

#### 1. GitHub Actions

```yaml
# .github/workflows/arxos-integration.yml
name: Arxos Integration

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/
    
    - name: Run integration tests
      run: |
        python tests/test_integration.py
    
    - name: Upload test results
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: test-results/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # Deploy to Arxos platform
        curl -X POST https://api.arxos.com/api/v1/deploy \
          -H "Authorization: Bearer ${{ secrets.ARXOS_API_KEY }}" \
          -H "Content-Type: application/json" \
          -d '{"environment": "production"}'
```

#### 2. Jenkins Integration

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Build') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Test') {
            steps {
                sh 'python -m pytest tests/'
                sh 'python tests/test_integration.py'
            }
        }
        
        stage('Deploy') {
            steps {
                script {
                    // Deploy to Arxos
                    sh '''
                        curl -X POST https://api.arxos.com/api/v1/deploy \\
                          -H "Authorization: Bearer ${ARXOS_API_KEY}" \\
                          -H "Content-Type: application/json" \\
                          -d '{"environment": "production"}'
                    '''
                }
            }
        }
    }
}
```

### Development Tools Integration

#### 1. VS Code Extension

```json
// .vscode/settings.json
{
    "arxos.apiKey": "your-api-key",
    "arxos.endpoint": "https://api.arxos.com/api/v1",
    "arxos.autoUpload": true,
    "arxos.autoExport": false,
    "arxos.format": "ifc-lite"
}
```

#### 2. PyCharm Integration

```python
# pycharm_integration.py
from services.pycharm_integration import PyCharmIntegration

pycharm = PyCharmIntegration()

# Auto-upload on save
pycharm.enable_auto_upload()

# Auto-export on changes
pycharm.enable_auto_export()

# Sync with Arxos
pycharm.sync_with_arxos()
```

---

## Testing & Validation

### Integration Testing

#### 1. API Testing

```python
import pytest
import requests

class TestArxosIntegration:
    def setup_method(self):
        self.base_url = "https://api.arxos.com/api/v1"
        self.headers = {
            "Authorization": "Bearer test-api-key",
            "Content-Type": "application/json"
        }
    
    def test_svg_upload(self):
        """Test SVG upload functionality"""
        with open("test_building.svg", "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{self.base_url}/upload/svg",
                headers=self.headers,
                files=files
            )
        
        assert response.status_code == 200
        assert "svg_id" in response.json()
    
    def test_bim_export(self):
        """Test BIM export functionality"""
        response = requests.post(
            f"{self.base_url}/export/create-job",
            headers=self.headers,
            json={
                "building_id": "test_building",
                "format": "ifc-lite"
            }
        )
        
        assert response.status_code == 200
        assert "job_id" in response.json()
    
    def test_security_integration(self):
        """Test security features integration"""
        response = requests.post(
            f"{self.base_url}/security/privacy/controls",
            headers=self.headers,
            json={
                "data": {"test": "data"},
                "classification": "internal"
            }
        )
        
        assert response.status_code == 200
        assert "privacy_metadata" in response.json()
```

#### 2. Performance Testing

```python
import time
import concurrent.futures

def test_api_performance():
    """Test API performance under load"""
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(100):
            future = executor.submit(upload_test_file)
            futures.append(future)
        
        # Wait for all requests to complete
        concurrent.futures.wait(futures)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Processed 100 requests in {total_time:.2f} seconds")
    print(f"Average response time: {total_time/100:.2f} seconds")

def upload_test_file():
    """Upload a test file"""
    with open("test_building.svg", "rb") as f:
        files = {"file": f}
        response = requests.post(
            "https://api.arxos.com/api/v1/upload/svg",
            headers=headers,
            files=files
        )
    return response.status_code
```

### Validation Testing

#### 1. Data Validation

```python
from services.validation_service import ValidationService

validator = ValidationService()

def test_data_validation():
    """Test data validation"""
    # Test SVG validation
    svg_valid = validator.validate_svg(svg_content)
    assert svg_valid.is_valid
    
    # Test BIM validation
    bim_valid = validator.validate_bim(bim_data)
    assert bim_valid.is_valid
    
    # Test export validation
    export_valid = validator.validate_export(export_data)
    assert export_valid.is_valid
```

#### 2. Security Validation

```python
from services.security_validator import SecurityValidator

security = SecurityValidator()

def test_security_validation():
    """Test security validation"""
    # Test encryption
    encryption_valid = security.validate_encryption(encrypted_data)
    assert encryption_valid.is_valid
    
    # Test privacy controls
    privacy_valid = security.validate_privacy_controls(protected_data)
    assert privacy_valid.is_valid
    
    # Test access control
    access_valid = security.validate_access_control(user_permissions)
    assert access_valid.is_valid
```

---

## Deployment Integration

### Docker Integration

#### 1. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 arxos && chown -R arxos:arxos /app
USER arxos

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["python", "main.py"]
```

#### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  arxos-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/arxos
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=arxos
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Kubernetes Integration

#### 1. Deployment YAML

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: arxos-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: arxos-api
  template:
    metadata:
      labels:
        app: arxos-api
    spec:
      containers:
      - name: arxos-api
        image: arxos/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: arxos-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 2. Service YAML

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: arxos-api-service
spec:
  selector:
    app: arxos-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Cloud Platform Integration

#### 1. AWS ECS Integration

```python
from services.aws_ecs_integration import AWSECSIntegration

ecs = AWSECSIntegration()

# Deploy to ECS
deployment = ecs.deploy_service(
    service_name="arxos-api",
    image_uri="arxos/api:latest",
    cpu="512",
    memory="1024",
    desired_count=3
)

print(f"Deployed service: {deployment.service_arn}")
```

#### 2. Azure Container Instances

```python
from services.azure_aci_integration import AzureACIIntegration

aci = AzureACIIntegration()

# Deploy to ACI
container_group = aci.deploy_container_group(
    name="arxos-api",
    image="arxos/api:latest",
    cpu="2",
    memory="4",
    ports=[8000]
)

print(f"Deployed container group: {container_group.id}")
```

---

## Troubleshooting

### Common Integration Issues

#### 1. Authentication Issues

**Problem:** API authentication failures
**Diagnosis:**
```python
# Check API key validity
response = requests.get(
    "https://api.arxos.com/api/v1/health",
    headers={"Authorization": "Bearer your-api-key"}
)

if response.status_code == 401:
    print("Invalid API key")
elif response.status_code == 403:
    print("Insufficient permissions")
```

**Solution:**
```python
# Regenerate API key
from services.auth_service import AuthService

auth = AuthService()
new_key = auth.regenerate_api_key("user123")
print(f"New API key: {new_key}")
```

#### 2. Rate Limiting Issues

**Problem:** API rate limit exceeded
**Diagnosis:**
```python
# Check rate limit headers
response = requests.get("https://api.arxos.com/api/v1/health")
rate_limit = response.headers.get("X-RateLimit-Remaining")
print(f"Remaining requests: {rate_limit}")
```

**Solution:**
```python
# Implement exponential backoff
import time
import random

def make_request_with_backoff(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code != 429:
                return response
            
            # Wait with exponential backoff
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)
            
        except Exception as e:
            print(f"Request failed: {e}")
    
    raise Exception("Max retries exceeded")
```

#### 3. File Upload Issues

**Problem:** Large file upload failures
**Diagnosis:**
```python
# Check file size limits
file_size = os.path.getsize("large_building.svg")
max_size = 50 * 1024 * 1024  # 50MB

if file_size > max_size:
    print(f"File too large: {file_size} bytes")
```

**Solution:**
```python
# Implement chunked upload
from services.chunked_upload import ChunkedUpload

uploader = ChunkedUpload()
uploader.upload_large_file("large_building.svg", chunk_size=1024*1024)
```

### Performance Issues

#### 1. Slow API Responses

**Problem:** API responses are slow
**Diagnosis:**
```python
import time

start_time = time.time()
response = requests.get("https://api.arxos.com/api/v1/health")
end_time = time.time()

response_time = end_time - start_time
if response_time > 5.0:
    print(f"Slow response: {response_time:.2f} seconds")
```

**Solution:**
```python
# Implement caching
from services.cache_service import CacheService

cache = CacheService()
cached_response = cache.get_cached_response("health")
if cached_response:
    return cached_response
else:
    response = requests.get("https://api.arxos.com/api/v1/health")
    cache.set_cached_response("health", response, ttl=300)
    return response
```

#### 2. Memory Issues

**Problem:** High memory usage during integration
**Diagnosis:**
```python
import psutil

memory_usage = psutil.virtual_memory()
if memory_usage.percent > 80:
    print(f"High memory usage: {memory_usage.percent}%")
```

**Solution:**
```python
# Implement memory management
from services.memory_manager import MemoryManager

memory = MemoryManager()
memory.optimize_memory_usage()
memory.clear_caches()
```

### Debugging Tools

#### 1. API Debugging

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Log all requests
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

# Make request with debug info
response = requests.get("https://api.arxos.com/api/v1/health")
print(f"Response: {response.text}")
```

#### 2. Integration Testing

```python
# Test integration components
def test_integration_components():
    """Test all integration components"""
    components = [
        "api_connection",
        "authentication",
        "file_upload",
        "data_export",
        "security_features"
    ]
    
    for component in components:
        result = test_component(component)
        print(f"{component}: {'PASS' if result else 'FAIL'}")
```

---

## Support Resources

### Documentation
- [API Documentation](./API_DOCUMENTATION.md)
- [User Guide](./USER_GUIDE.md)
- [Admin Guide](./ADMIN_GUIDE.md)

### SDKs and Libraries
- **Python SDK**: `pip install arxos-sdk`
- **JavaScript SDK**: `npm install arxos-sdk`
- **iOS SDK**: Available via CocoaPods
- **Android SDK**: Available via Maven

### Community
- **GitHub**: https://github.com/arxos/arx-svg-parser
- **Discussions**: https://github.com/arxos/arx-svg-parser/discussions
- **Issues**: https://github.com/arxos/arx-svg-parser/issues

### Support
- **Email**: integration@arxos.com
- **Documentation**: https://docs.arxos.com
- **Training**: https://training.arxos.com

---

**Version**: 1.0.0  
**Last Updated**: December 19, 2024  
**Contact**: integration@arxos.com 