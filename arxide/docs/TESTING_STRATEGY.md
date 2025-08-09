# ArxIDE Testing Strategy

## 🎯 Overview

This document outlines the comprehensive testing strategy for ArxIDE, covering unit tests, integration tests, end-to-end tests, performance tests, and security tests. The strategy ensures high code quality, reliability, and user satisfaction.

## 📋 Testing Pyramid

### 1. Unit Tests (70% of test coverage)
- **Purpose**: Test individual functions and components in isolation
- **Framework**: Jest for TypeScript/JavaScript, pytest for Python, Go testing for Go
- **Coverage Target**: 90%+ code coverage
- **Execution**: Fast (< 1 second per test)

### 2. Integration Tests (20% of test coverage)
- **Purpose**: Test interactions between components and services
- **Framework**: Jest with supertest, pytest with testcontainers, Go with testify
- **Coverage Target**: All API endpoints and service interactions
- **Execution**: Medium speed (< 30 seconds per test)

### 3. End-to-End Tests (10% of test coverage)
- **Purpose**: Test complete user workflows
- **Framework**: Playwright for browser automation
- **Coverage Target**: Critical user journeys
- **Execution**: Slow (< 5 minutes per test)

## 🧪 Unit Testing Strategy

### 1. Desktop Application (Electron/TypeScript)

#### Component Testing
```typescript
// Component Test Example
import { render, screen, fireEvent } from '@testing-library/react'
import { SVGXCanvas } from '../components/SVGXCanvas'

describe('SVGXCanvas', () => {
  test('renders canvas with initial state', () => {
    render(<SVGXCanvas initialContent="<svg></svg>" />)

    expect(screen.getByTestId('svgx-canvas')).toBeInTheDocument()
    expect(screen.getByTestId('canvas-content')).toHaveTextContent('<svg></svg>')
  })

  test('handles element selection', () => {
    const onElementSelect = jest.fn()
    render(<SVGXCanvas onElementSelect={onElementSelect} />)

    const element = screen.getByTestId('svg-element')
    fireEvent.click(element)

    expect(onElementSelect).toHaveBeenCalledWith('element-id')
  })

  test('updates canvas on content change', () => {
    const { rerender } = render(<SVGXCanvas content="<svg></svg>" />)

    rerender(<SVGXCanvas content="<svg><rect/></svg>" />)

    expect(screen.getByTestId('canvas-content')).toHaveTextContent('<rect/>')
  })
})
```

#### Service Testing
```typescript
// Service Test Example
import { FileService } from '../services/FileService'
import { mockFileSystem } from '../__mocks__/fileSystem'

describe('FileService', () => {
  let fileService: FileService

  beforeEach(() => {
    fileService = new FileService(mockFileSystem)
  })

  test('loads SVGX file correctly', async () => {
    const content = await fileService.loadFile('test.svgx')

    expect(content).toContain('<svgx>')
    expect(content).toContain('<building>')
  })

  test('saves file with proper formatting', async () => {
    const content = '<svgx><building/></svgx>'
    await fileService.saveFile('test.svgx', content)

    const savedContent = await fileService.loadFile('test.svgx')
    expect(savedContent).toBe(content)
  })

  test('validates file format', async () => {
    const invalidContent = '<invalid>content</invalid>'

    await expect(fileService.saveFile('test.svgx', invalidContent))
      .rejects.toThrow('Invalid SVGX format')
  })
})
```

### 2. Backend Services (Go)

#### API Testing
```go
// API Test Example
package api

import (
    "testing"
    "net/http"
    "net/http/httptest"
    "encoding/json"
    "github.com/gin-gonic/gin"
    "github.com/stretchr/testify/assert"
)

func TestUserAPI(t *testing.T) {
    gin.SetMode(gin.TestMode)
    router := setupRouter()

    t.Run("GET /api/users/:id", func(t *testing.T) {
        req, _ := http.NewRequest("GET", "/api/users/123", nil)
        w := httptest.NewRecorder()
        router.ServeHTTP(w, req)

        assert.Equal(t, http.StatusOK, w.Code)

        var response UserResponse
        json.Unmarshal(w.Body.Bytes(), &response)

        assert.Equal(t, "123", response.ID)
        assert.NotEmpty(t, response.Username)
    })

    t.Run("POST /api/users", func(t *testing.T) {
        userData := `{"username":"testuser","email":"test@example.com"}`
        req, _ := http.NewRequest("POST", "/api/users", strings.NewReader(userData))
        req.Header.Set("Content-Type", "application/json")
        w := httptest.NewRecorder()
        router.ServeHTTP(w, req)

        assert.Equal(t, http.StatusCreated, w.Code)

        var response UserResponse
        json.Unmarshal(w.Body.Bytes(), &response)

        assert.NotEmpty(t, response.ID)
        assert.Equal(t, "testuser", response.Username)
    })
}
```

#### Service Testing
```go
// Service Test Example
package services

import (
    "testing"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
)

type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) GetByID(id string) (*User, error) {
    args := m.Called(id)
    return args.Get(0).(*User), args.Error(1)
}

func TestUserService(t *testing.T) {
    mockRepo := new(MockUserRepository)
    userService := NewUserService(mockRepo)

    t.Run("GetUserByID", func(t *testing.T) {
        expectedUser := &User{
            ID:       "123",
            Username: "testuser",
            Email:    "test@example.com",
        }

        mockRepo.On("GetByID", "123").Return(expectedUser, nil)

        user, err := userService.GetUserByID("123")

        assert.NoError(t, err)
        assert.Equal(t, expectedUser, user)
        mockRepo.AssertExpectations(t)
    })
}
```

### 3. AI/CAD Services (Python)

#### Service Testing
```python
# Service Test Example
import pytest
from unittest.mock import Mock, patch
from services.arxos_agent import ArxosAgent
from services.svgx_engine import SVGXEngine

class TestArxosAgent:
    def setup_method(self):
        self.agent = ArxosAgent()

    def test_process_natural_language_command(self):
        command = "Create a new electrical panel in room 101"
        result = self.agent.process_command(command)

        assert result.success is True
        assert "panel" in result.svgx_code.lower()
        assert "electrical" in result.svgx_code.lower()

    def test_validate_command(self):
        invalid_command = "Invalid command"
        result = self.agent.validate_command(invalid_command)

        assert result.is_valid is False
        assert "unrecognized" in result.error_message.lower()

class TestSVGXEngine:
    def setup_method(self):
        self.engine = SVGXEngine()

    def test_parse_svgx_content(self):
        svgx_content = """
        <svgx>
            <building>
                <floor level="1">
                    <room id="101" name="Conference Room"/>
                </floor>
            </building>
        </svgx>
        """

        result = self.engine.parse_content(svgx_content)

        assert result.is_valid is True
        assert len(result.rooms) == 1
        assert result.rooms[0].id == "101"

    def test_generate_svgx_from_components(self):
        components = [
            {"type": "room", "id": "101", "name": "Office"},
            {"type": "panel", "id": "E001", "room": "101"}
        ]

        svgx_content = self.engine.generate_svgx(components)

        assert "<svgx>" in svgx_content
        assert "room id=\"101\"" in svgx_content
        assert "panel id=\"E001\"" in svgx_content
```

## 🔗 Integration Testing Strategy

### 1. API Integration Tests

#### REST API Testing
```typescript
// API Integration Test Example
import request from 'supertest'
import { app } from '../src/app'
import { setupTestDatabase, teardownTestDatabase } from './testUtils'

describe('API Integration Tests', () => {
  beforeAll(async () => {
    await setupTestDatabase()
  })

  afterAll(async () => {
    await teardownTestDatabase()
  })

  describe('Building API', () => {
    test('creates building with valid data', async () => {
      const buildingData = {
        name: 'Test Building',
        address: '123 Test St',
        floors: 3
      }

      const response = await request(app)
        .post('/api/buildings')
        .send(buildingData)
        .expect(201)

      expect(response.body.id).toBeDefined()
      expect(response.body.name).toBe(buildingData.name)
    })

    test('retrieves building by ID', async () => {
      const buildingId = 'test-building-id'

      const response = await request(app)
        .get(`/api/buildings/${buildingId}`)
        .expect(200)

      expect(response.body.id).toBe(buildingId)
      expect(response.body.name).toBeDefined()
    })
  })

  describe('File API', () => {
    test('uploads SVGX file', async () => {
      const fileContent = '<svgx><building/></svgx>'

      const response = await request(app)
        .post('/api/files/upload')
        .attach('file', Buffer.from(fileContent), 'test.svgx')
        .expect(200)

      expect(response.body.fileId).toBeDefined()
      expect(response.body.filename).toBe('test.svgx')
    })
  })
})
```

### 2. Service Integration Tests

#### Microservice Communication
```python
# Service Integration Test Example
import pytest
import asyncio
from httpx import AsyncClient
from services.main import app
from services.database import get_test_database

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_db():
    db = get_test_database()
    yield db
    await db.close()

class TestArxosAgentIntegration:
    async def test_natural_language_to_svgx_flow(self, client, test_db):
        # Test complete flow from natural language to SVGX
        command_data = {
            "command": "Add an electrical panel to room 101",
            "building_id": "test-building"
        }

        response = await client.post("/api/agent/command", json=command_data)
        assert response.status_code == 200

        result = response.json()
        assert result["success"] is True
        assert "panel" in result["svgx_code"]

        # Verify SVGX was saved to database
        saved_svgx = await test_db.get_svgx_by_building("test-building")
        assert saved_svgx is not None
        assert "panel" in saved_svgx.content

class TestSVGXEngineIntegration:
    async def test_svgx_processing_pipeline(self, client):
        # Test SVGX processing pipeline
        svgx_content = """
        <svgx>
            <building id="test-building">
                <floor level="1">
                    <room id="101">
                        <panel id="E001" type="electrical"/>
                    </room>
                </floor>
            </building>
        </svgx>
        """

        # Process SVGX
        response = await client.post("/api/svgx/process", json={
            "content": svgx_content
        })
        assert response.status_code == 200

        result = response.json()
        assert result["valid"] is True
        assert len(result["components"]) == 3  # building, floor, room, panel
```

## 🌐 End-to-End Testing Strategy

### 1. User Workflow Testing

#### Complete User Journeys
```typescript
// E2E Test Example
import { test, expect } from '@playwright/test'

test.describe('ArxIDE User Workflows', () => {
  test('complete building design workflow', async ({ page }) => {
    // 1. Login
    await page.goto('/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')

    // 2. Create new building
    await page.click('[data-testid="new-building-button"]')
    await page.fill('[data-testid="building-name"]', 'Test Building')
    await page.fill('[data-testid="building-address"]', '123 Test St')
    await page.click('[data-testid="create-building-button"]')

    // 3. Add floor
    await page.click('[data-testid="add-floor-button"]')
    await page.fill('[data-testid="floor-level"]', '1')
    await page.click('[data-testid="save-floor-button"]')

    // 4. Add room
    await page.click('[data-testid="add-room-button"]')
    await page.fill('[data-testid="room-name"]', 'Conference Room')
    await page.fill('[data-testid="room-number"]', '101')
    await page.click('[data-testid="save-room-button"]')

    // 5. Add electrical panel
    await page.click('[data-testid="add-panel-button"]')
    await page.selectOption('[data-testid="panel-type"]', 'electrical')
    await page.fill('[data-testid="panel-id"]', 'E001')
    await page.click('[data-testid="save-panel-button"]')

    // 6. Verify building structure
    await expect(page.locator('[data-testid="building-name"]')).toHaveText('Test Building')
    await expect(page.locator('[data-testid="floor-1"]')).toBeVisible()
    await expect(page.locator('[data-testid="room-101"]')).toBeVisible()
    await expect(page.locator('[data-testid="panel-E001"]')).toBeVisible()
  })

  test('natural language command workflow', async ({ page }) => {
    // 1. Login and open building
    await page.goto('/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')

    await page.click('[data-testid="building-item"]')

    // 2. Open chat interface
    await page.click('[data-testid="chat-button"]')

    // 3. Send natural language command
    await page.fill('[data-testid="chat-input"]', 'Add a lighting fixture to room 101')
    await page.click('[data-testid="send-button"]')

    // 4. Verify command processing
    await expect(page.locator('[data-testid="chat-message"]')).toContainText('Processing command')
    await expect(page.locator('[data-testid="chat-message"]')).toContainText('Added lighting fixture')

    // 5. Verify visual update
    await expect(page.locator('[data-testid="lighting-fixture"]')).toBeVisible()
  })
})
```

### 2. Cross-Platform Testing

#### Platform-Specific Tests
```typescript
// Platform Test Example
import { test, expect } from '@playwright/test'

test.describe('Cross-Platform Compatibility', () => {
  test('works on Windows', async ({ page }) => {
    // Test Windows-specific features
    await page.goto('/')
    await expect(page.locator('[data-testid="windows-compatible"]')).toBeVisible()
  })

  test('works on macOS', async ({ page }) => {
    // Test macOS-specific features
    await page.goto('/')
    await expect(page.locator('[data-testid="macos-compatible"]')).toBeVisible()
  })

  test('works on Linux', async ({ page }) => {
    // Test Linux-specific features
    await page.goto('/')
    await expect(page.locator('[data-testid="linux-compatible"]')).toBeVisible()
  })
})
```

## ⚡ Performance Testing Strategy

### 1. Load Testing

#### API Performance Tests
```typescript
// Performance Test Example
import { test, expect } from '@playwright/test'

test.describe('Performance Tests', () => {
  test('API response time under load', async ({ request }) => {
    const startTime = Date.now()

    // Make multiple concurrent requests
    const promises = Array.from({ length: 100 }, () =>
      request.get('/api/buildings')
    )

    const responses = await Promise.all(promises)
    const endTime = Date.now()

    // Verify all requests succeeded
    responses.forEach(response => {
      expect(response.status()).toBe(200)
    })

    // Verify response time is under threshold
    const averageResponseTime = (endTime - startTime) / responses.length
    expect(averageResponseTime).toBeLessThan(1000) // 1 second
  })

  test('large file processing performance', async ({ request }) => {
    const largeSvgxContent = generateLargeSVGX(1000) // 1000 components

    const startTime = Date.now()
    const response = await request.post('/api/svgx/process', {
      data: { content: largeSvgxContent }
    })
    const endTime = Date.now()

    expect(response.status()).toBe(200)
    expect(endTime - startTime).toBeLessThan(5000) // 5 seconds
  })
})
```

### 2. Memory Testing

#### Memory Leak Detection
```typescript
// Memory Test Example
import { test, expect } from '@playwright/test'

test.describe('Memory Tests', () => {
  test('no memory leaks during file operations', async ({ page }) => {
    const initialMemory = await page.evaluate(() => performance.memory?.usedJSHeapSize || 0)

    // Perform multiple file operations
    for (let i = 0; i < 10; i++) {
      await page.click('[data-testid="new-file-button"]')
      await page.fill('[data-testid="file-content"]', `<svgx><component id="${i}"/></svgx>`)
      await page.click('[data-testid="save-file-button"]')
      await page.waitForTimeout(100)
    }

    const finalMemory = await page.evaluate(() => performance.memory?.usedJSHeapSize || 0)
    const memoryIncrease = finalMemory - initialMemory

    // Memory increase should be reasonable (< 50MB)
    expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024)
  })
})
```

## 🔒 Security Testing Strategy

### 1. Authentication Testing

#### Security Test Examples
```typescript
// Security Test Example
import { test, expect } from '@playwright/test'

test.describe('Security Tests', () => {
  test('prevents unauthorized access', async ({ page }) => {
    // Try to access protected resource without login
    await page.goto('/api/buildings')

    // Should redirect to login
    await expect(page).toHaveURL(/.*login.*/)
  })

  test('validates input sanitization', async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="email"]', 'test@example.com')
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')

    // Try to inject malicious content
    const maliciousContent = '<script>alert("xss")</script>'
    await page.fill('[data-testid="building-name"]', maliciousContent)
    await page.click('[data-testid="save-building-button"]')

    // Should sanitize and save safely
    await expect(page.locator('[data-testid="building-name"]')).not.toContainText('<script>')
  })

  test('prevents SQL injection', async ({ page }) => {
    await page.goto('/login')
    await page.fill('[data-testid="email"]', "'; DROP TABLE users; --")
    await page.fill('[data-testid="password"]', 'password123')
    await page.click('[data-testid="login-button"]')

    // Should handle injection attempt safely
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Invalid credentials')
  })
})
```

## 📊 Test Reporting & Metrics

### 1. Coverage Reporting

#### Coverage Configuration
```typescript
// Coverage Configuration
export default {
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
    '!src/test/**/*',
    '!src/**/index.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    },
    './src/services/': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90
    }
  },
  coverageReporters: ['text', 'lcov', 'html'],
  coverageDirectory: 'coverage'
}
```

### 2. Test Metrics Dashboard

#### Key Metrics
```typescript
// Test Metrics Interface
interface TestMetrics {
  // Coverage metrics
  totalCoverage: number
  lineCoverage: number
  branchCoverage: number
  functionCoverage: number

  // Performance metrics
  averageTestDuration: number
  slowestTests: TestResult[]
  fastestTests: TestResult[]

  // Quality metrics
  testPassRate: number
  flakyTests: TestResult[]
  failingTests: TestResult[]

  // Security metrics
  securityTestPassRate: number
  vulnerabilityCount: number
  securityIssues: SecurityIssue[]
}
```

## 🚀 CI/CD Integration

### 1. Automated Testing Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
          POSTGRES_DB: arxide_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
    - uses: actions/checkout@v4

    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'

    - name: Setup Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        npm ci
        go mod download
        pip install -r services/requirements.txt

    - name: Run unit tests
      run: |
        npm run test:unit
        npm run test:coverage

    - name: Run integration tests
      run: |
        npm run test:integration

    - name: Run E2E tests
      run: |
        npm run test:e2e

    - name: Run security tests
      run: |
        npm run test:security

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info
        flags: unittests
        name: codecov-umbrella

    - name: Generate test report
      run: |
        npm run test:report
```

This comprehensive testing strategy ensures that ArxIDE maintains high quality, reliability, and security throughout development and deployment.
