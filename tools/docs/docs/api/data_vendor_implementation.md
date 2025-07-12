# Data Vendor API Implementation Guide

## Overview

This guide provides comprehensive information for data purchasers implementing the Arxos Data Vendor API. It covers authentication, rate limiting, data access patterns, monitoring, and best practices for production use.

## Quick Start

### 1. Get Your API Key

1. Contact Arxos sales team to establish a partnership
2. Complete the vendor onboarding process
3. Receive your API key and access credentials
4. Review your access level and rate limits

### 2. Basic Implementation

```javascript
// JavaScript/Node.js Example
const axios = require('axios');

const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://api.arxos.io/v1';

const apiClient = axios.create({
    baseURL: BASE_URL,
    headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
});

// Get available buildings
async function getBuildings() {
    try {
        const response = await apiClient.get('/api/vendor/buildings');
        return response.data;
    } catch (error) {
        console.error('Error fetching buildings:', error.response.data);
        throw error;
    }
}
```

```python
# Python Example
import requests

API_KEY = 'your_api_key_here'
BASE_URL = 'https://api.arxos.io/v1'

headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
}

def get_buildings():
    try:
        response = requests.get(f'{BASE_URL}/api/vendor/buildings', headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Error fetching buildings: {e}')
        raise
```

```go
// Go Example
package main

import (
    "fmt"
    "net/http"
    "io/ioutil"
)

const (
    API_KEY  = "your_api_key_here"
    BASE_URL = "https://api.arxos.io/v1"
)

func getBuildings() ([]byte, error) {
    client := &http.Client{}
    
    req, err := http.NewRequest("GET", BASE_URL+"/api/vendor/buildings", nil)
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("X-API-Key", API_KEY)
    req.Header.Set("Content-Type", "application/json")
    
    resp, err := client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        return nil, fmt.Errorf("API request failed with status: %d", resp.StatusCode)
    }
    
    return ioutil.ReadAll(resp.Body)
}
```

## Authentication

### API Key Format

API keys follow the format: `arx_[timestamp]_[random_string]`

Example: `arx_1234567890_abcdef123456`

### Security Best Practices

1. **Store API keys securely:**
   ```bash
   # Use environment variables
   export ARXOS_API_KEY="your_api_key_here"
   ```

2. **Never expose API keys in client-side code**
3. **Rotate API keys regularly**
4. **Use HTTPS for all API calls**
5. **Monitor API key usage for suspicious activity**

### Error Handling

```javascript
// Comprehensive error handling
async function makeAPIRequest(endpoint) {
    try {
        const response = await apiClient.get(endpoint);
        return response.data;
    } catch (error) {
        if (error.response) {
            switch (error.response.status) {
                case 401:
                    throw new Error('Invalid API key or authentication failed');
                case 403:
                    throw new Error('Insufficient permissions for this endpoint');
                case 429:
                    const retryAfter = error.response.headers['retry-after'];
                    throw new Error(`Rate limit exceeded. Retry after ${retryAfter} seconds`);
                case 500:
                    throw new Error('Internal server error. Please try again later');
                default:
                    throw new Error(`API request failed: ${error.response.data.error}`);
            }
        } else if (error.request) {
            throw new Error('Network error. Please check your connection');
        } else {
            throw new Error('Request configuration error');
        }
    }
}
```

## Rate Limiting

### Understanding Rate Limits

Rate limits are enforced on a rolling window basis per API key:

- **Basic:** 1,000 requests/hour
- **Premium:** 5,000 requests/hour  
- **Enterprise:** 20,000 requests/hour

### Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1642248000
```

### Implementing Rate Limiting

```javascript
// Rate limiting implementation
class RateLimitedAPIClient {
    constructor(apiKey, requestsPerHour) {
        this.apiKey = apiKey;
        this.requestsPerHour = requestsPerHour;
        this.requestCount = 0;
        this.resetTime = Date.now() + 3600000; // 1 hour from now
    }

    async makeRequest(endpoint) {
        // Check if we need to reset the counter
        if (Date.now() > this.resetTime) {
            this.requestCount = 0;
            this.resetTime = Date.now() + 3600000;
        }

        // Check if we're at the limit
        if (this.requestCount >= this.requestsPerHour) {
            const waitTime = this.resetTime - Date.now();
            throw new Error(`Rate limit exceeded. Wait ${Math.ceil(waitTime / 1000)} seconds`);
        }

        this.requestCount++;
        
        try {
            const response = await apiClient.get(endpoint);
            
            // Update rate limit info from headers
            const remaining = response.headers['x-ratelimit-remaining'];
            const reset = response.headers['x-ratelimit-reset'];
            
            if (remaining !== undefined) {
                this.requestCount = this.requestsPerHour - parseInt(remaining);
            }
            
            return response.data;
        } catch (error) {
            if (error.response?.status === 429) {
                const retryAfter = error.response.headers['retry-after'];
                throw new Error(`Rate limit exceeded. Retry after ${retryAfter} seconds`);
            }
            throw error;
        }
    }
}
```

## Data Access Patterns

### 1. Building Discovery

```javascript
// Get all available buildings
async function discoverBuildings() {
    const buildings = await makeAPIRequest('/api/vendor/buildings');
    
    console.log(`Found ${buildings.buildings.length} buildings`);
    
    // Filter by building type
    const officeBuildings = buildings.buildings.filter(b => 
        b.building_type === 'Office'
    );
    
    // Filter by status
    const activeBuildings = buildings.buildings.filter(b => 
        b.status === 'active'
    );
    
    return activeBuildings;
}
```

### 2. Asset Inventory Retrieval

```javascript
// Get building inventory with pagination
async function getBuildingInventory(buildingId, options = {}) {
    const params = new URLSearchParams({
        limit: options.limit || 100,
        offset: options.offset || 0,
        ...(options.category && { category: options.category }),
        ...(options.status && { status: options.status })
    });
    
    const inventory = await makeAPIRequest(
        `/api/vendor/buildings/${buildingId}/inventory?${params}`
    );
    
    return {
        building: inventory.building,
        assets: inventory.inventory,
        pagination: inventory.pagination
    };
}

// Process all assets in a building
async function processAllAssets(buildingId) {
    let offset = 0;
    const limit = 100;
    let allAssets = [];
    
    while (true) {
        const result = await getBuildingInventory(buildingId, { limit, offset });
        allAssets = allAssets.concat(result.assets);
        
        if (!result.pagination.has_more) {
            break;
        }
        
        offset += limit;
    }
    
    return allAssets;
}
```

### 3. Data Analysis and Filtering

```javascript
// Analyze building assets by system
function analyzeAssetsBySystem(assets) {
    const systemAnalysis = {};
    
    assets.forEach(asset => {
        const system = asset.system;
        if (!systemAnalysis[system]) {
            systemAnalysis[system] = {
                count: 0,
                totalValue: 0,
                averageAge: 0,
                assetTypes: {}
            };
        }
        
        systemAnalysis[system].count++;
        systemAnalysis[system].totalValue += asset.estimated_value || 0;
        
        if (!systemAnalysis[system].assetTypes[asset.asset_type]) {
            systemAnalysis[system].assetTypes[asset.asset_type] = 0;
        }
        systemAnalysis[system].assetTypes[asset.asset_type]++;
    });
    
    // Calculate averages
    Object.keys(systemAnalysis).forEach(system => {
        const data = systemAnalysis[system];
        data.averageAge = data.totalValue / data.count;
    });
    
    return systemAnalysis;
}

// Filter assets by criteria
function filterAssets(assets, filters) {
    return assets.filter(asset => {
        if (filters.system && asset.system !== filters.system) return false;
        if (filters.assetType && asset.asset_type !== filters.assetType) return false;
        if (filters.status && asset.status !== filters.status) return false;
        if (filters.minValue && asset.estimated_value < filters.minValue) return false;
        if (filters.maxValue && asset.estimated_value > filters.maxValue) return false;
        if (filters.minAge && asset.age < filters.minAge) return false;
        if (filters.maxAge && asset.age > filters.maxAge) return false;
        return true;
    });
}
```

## Monitoring and Logging

### 1. Request Logging

```javascript
// Comprehensive request logging
class APIMonitor {
    constructor() {
        this.requestLog = [];
        this.errorLog = [];
    }

    logRequest(endpoint, method, status, responseTime, timestamp = Date.now()) {
        this.requestLog.push({
            endpoint,
            method,
            status,
            responseTime,
            timestamp
        });
        
        // Keep only last 1000 requests
        if (this.requestLog.length > 1000) {
            this.requestLog = this.requestLog.slice(-1000);
        }
    }

    logError(endpoint, method, error, timestamp = Date.now()) {
        this.errorLog.push({
            endpoint,
            method,
            error: error.message,
            timestamp
        });
    }

    getMetrics() {
        const now = Date.now();
        const lastHour = now - 3600000;
        
        const recentRequests = this.requestLog.filter(
            req => req.timestamp > lastHour
        );
        
        const recentErrors = this.errorLog.filter(
            err => err.timestamp > lastHour
        );
        
        return {
            requestsLastHour: recentRequests.length,
            errorsLastHour: recentErrors.length,
            averageResponseTime: recentRequests.length > 0 
                ? recentRequests.reduce((sum, req) => sum + req.responseTime, 0) / recentRequests.length
                : 0,
            successRate: recentRequests.length > 0
                ? (recentRequests.filter(req => req.status >= 200 && req.status < 300).length / recentRequests.length) * 100
                : 100
        };
    }
}
```

### 2. Performance Monitoring

```javascript
// Performance monitoring wrapper
async function monitoredRequest(endpoint, options = {}) {
    const startTime = Date.now();
    const monitor = new APIMonitor();
    
    try {
        const response = await apiClient.get(endpoint, options);
        const responseTime = Date.now() - startTime;
        
        monitor.logRequest(
            endpoint,
            'GET',
            response.status,
            responseTime
        );
        
        return response.data;
    } catch (error) {
        monitor.logError(endpoint, 'GET', error);
        throw error;
    }
}
```

### 3. Health Checks

```javascript
// API health check
async function checkAPIHealth() {
    try {
        const startTime = Date.now();
        const response = await apiClient.get('/api/vendor/buildings?limit=1');
        const responseTime = Date.now() - startTime;
        
        return {
            status: 'healthy',
            responseTime,
            timestamp: new Date().toISOString()
        };
    } catch (error) {
        return {
            status: 'unhealthy',
            error: error.message,
            timestamp: new Date().toISOString()
        };
    }
}

// Scheduled health checks
setInterval(async () => {
    const health = await checkAPIHealth();
    console.log('API Health:', health);
    
    if (health.status === 'unhealthy') {
        // Send alert
        console.error('API is unhealthy:', health.error);
    }
}, 300000); // Check every 5 minutes
```

## Data Processing and Storage

### 1. Efficient Data Storage

```javascript
// Optimized data storage with indexing
class AssetDatabase {
    constructor() {
        this.assets = new Map();
        this.buildings = new Map();
        this.indexes = {
            bySystem: new Map(),
            byType: new Map(),
            byStatus: new Map(),
            byBuilding: new Map()
        };
    }

    addAsset(asset) {
        this.assets.set(asset.id, asset);
        
        // Update indexes
        this.updateIndex('bySystem', asset.system, asset.id);
        this.updateIndex('byType', asset.asset_type, asset.id);
        this.updateIndex('byStatus', asset.status, asset.id);
        this.updateIndex('byBuilding', asset.building_id, asset.id);
    }

    updateIndex(indexName, key, assetId) {
        if (!this.indexes[indexName].has(key)) {
            this.indexes[indexName].set(key, new Set());
        }
        this.indexes[indexName].get(key).add(assetId);
    }

    queryAssets(filters) {
        let resultSet = new Set();
        let isFirstFilter = true;
        
        Object.entries(filters).forEach(([key, value]) => {
            const indexKey = `by${key.charAt(0).toUpperCase() + key.slice(1)}`;
            if (this.indexes[indexKey] && this.indexes[indexKey].has(value)) {
                const assetIds = this.indexes[indexKey].get(value);
                
                if (isFirstFilter) {
                    resultSet = new Set(assetIds);
                    isFirstFilter = false;
                } else {
                    resultSet = new Set([...resultSet].filter(id => assetIds.has(id)));
                }
            }
        });
        
        return Array.from(resultSet).map(id => this.assets.get(id));
    }
}
```

### 2. Data Synchronization

```javascript
// Incremental data sync
class DataSync {
    constructor() {
        this.lastSync = new Map();
        this.syncInterval = 300000; // 5 minutes
    }

    async syncBuildingData(buildingId) {
        const lastSyncTime = this.lastSync.get(buildingId) || 0;
        
        try {
            // Get updated data since last sync
            const params = new URLSearchParams({
                updated_since: new Date(lastSyncTime).toISOString()
            });
            
            const response = await apiClient.get(
                `/api/vendor/buildings/${buildingId}/inventory?${params}`
            );
            
            // Process updates
            await this.processUpdates(buildingId, response.data.inventory);
            
            // Update last sync time
            this.lastSync.set(buildingId, Date.now());
            
            console.log(`Synced ${response.data.inventory.length} assets for building ${buildingId}`);
            
        } catch (error) {
            console.error(`Sync failed for building ${buildingId}:`, error);
            throw error;
        }
    }

    async processUpdates(buildingId, assets) {
        // Process asset updates
        for (const asset of assets) {
            await this.updateAsset(asset);
        }
    }

    async updateAsset(asset) {
        // Update local database
        // This would integrate with your existing data storage
        console.log(`Updating asset ${asset.id}`);
    }
}
```

## Error Handling and Recovery

### 1. Retry Logic

```javascript
// Exponential backoff retry
async function retryRequest(requestFn, maxRetries = 3, baseDelay = 1000) {
    let lastError;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await requestFn();
        } catch (error) {
            lastError = error;
            
            if (attempt === maxRetries) {
                throw error;
            }
            
            // Don't retry on client errors (4xx)
            if (error.response && error.response.status >= 400 && error.response.status < 500) {
                throw error;
            }
            
            // Calculate delay with exponential backoff
            const delay = baseDelay * Math.pow(2, attempt);
            console.log(`Request failed, retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries + 1})`);
            
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    
    throw lastError;
}

// Usage
const buildings = await retryRequest(() => 
    makeAPIRequest('/api/vendor/buildings')
);
```

### 2. Circuit Breaker Pattern

```javascript
// Circuit breaker implementation
class CircuitBreaker {
    constructor(failureThreshold = 5, resetTimeout = 60000) {
        this.failureThreshold = failureThreshold;
        this.resetTimeout = resetTimeout;
        this.failureCount = 0;
        this.lastFailureTime = null;
        this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    }

    async execute(requestFn) {
        if (this.state === 'OPEN') {
            if (Date.now() - this.lastFailureTime > this.resetTimeout) {
                this.state = 'HALF_OPEN';
            } else {
                throw new Error('Circuit breaker is OPEN');
            }
        }

        try {
            const result = await requestFn();
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }

    onSuccess() {
        this.failureCount = 0;
        this.state = 'CLOSED';
    }

    onFailure() {
        this.failureCount++;
        this.lastFailureTime = Date.now();
        
        if (this.failureCount >= this.failureThreshold) {
            this.state = 'OPEN';
        }
    }
}
```

## Best Practices

### 1. Performance Optimization

- **Use pagination** for large datasets
- **Implement caching** for frequently accessed data
- **Batch requests** when possible
- **Use appropriate timeouts** for different operations
- **Monitor response times** and optimize slow queries

### 2. Data Management

- **Validate data** before processing
- **Handle missing or null values** gracefully
- **Implement data versioning** for critical datasets
- **Backup important data** regularly
- **Monitor data quality** and consistency

### 3. Security

- **Rotate API keys** regularly
- **Monitor for suspicious activity**
- **Use HTTPS** for all communications
- **Implement proper error handling** to avoid information leakage
- **Log security events** for audit purposes

### 4. Monitoring and Alerting

- **Set up alerts** for rate limit violations
- **Monitor API response times**
- **Track error rates** and types
- **Set up health checks** for critical endpoints
- **Implement logging** for debugging and audit trails

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check API key validity
   - Verify API key format
   - Ensure API key is not expired

2. **403 Forbidden**
   - Check access level permissions
   - Verify endpoint access rights
   - Contact support for access level upgrades

3. **429 Too Many Requests**
   - Implement rate limiting
   - Use exponential backoff
   - Consider upgrading access level

4. **500 Internal Server Error**
   - Retry with exponential backoff
   - Check API status page
   - Contact support if persistent

### Debugging Tools

```javascript
// Debug logging utility
function debugRequest(endpoint, options = {}) {
    console.log('API Request:', {
        endpoint,
        method: options.method || 'GET',
        headers: options.headers,
        timestamp: new Date().toISOString()
    });
    
    return apiClient.get(endpoint, options).then(response => {
        console.log('API Response:', {
            status: response.status,
            headers: response.headers,
            dataSize: JSON.stringify(response.data).length,
            timestamp: new Date().toISOString()
        });
        return response;
    }).catch(error => {
        console.error('API Error:', {
            status: error.response?.status,
            message: error.message,
            timestamp: new Date().toISOString()
        });
        throw error;
    });
}
```

## Support and Resources

### Getting Help

- **Documentation:** https://docs.arxos.io/api
- **API Status:** https://status.arxos.io
- **Support Email:** api-support@arxos.io
- **Community Forum:** https://community.arxos.io

### SDKs and Libraries

- **JavaScript/Node.js:** https://github.com/arxos/arxos-js-sdk
- **Python:** https://github.com/arxos/arxos-python-sdk
- **Go:** https://github.com/arxos/arxos-go-sdk
- **Java:** https://github.com/arxos/arxos-java-sdk
- **.NET:** https://github.com/arxos/arxos-dotnet-sdk

### Rate Limits and Pricing

| Access Level | Rate Limit | Monthly Cost | Features |
|--------------|------------|--------------|----------|
| Basic | 1,000 req/hour | $50 | Public building data |
| Premium | 5,000 req/hour | $150 | Basic + detailed inventory |
| Enterprise | 20,000 req/hour | $500 | All data + priority support |

### Changelog

- **v1.2.0** - Added building summary endpoints
- **v1.1.0** - Enhanced rate limiting and monitoring
- **v1.0.0** - Initial API release 