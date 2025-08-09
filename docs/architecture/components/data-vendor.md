# Data Vendor API: Comprehensive System Design

## 🎯 **Executive Summary**

The Arxos Data Vendor API system enables external data purchasers to query any object from any building in any quantity through both traditional API calls and natural language chat interfaces. This comprehensive system builds upon existing infrastructure while adding advanced NLP capabilities, real-time analytics, and enterprise-grade security.

---

## 📊 **Current State vs. Target State**

### ✅ **What's Already Built**
- **Authentication System**: API key-based auth with role-based access control
- **Rate Limiting**: Configurable limits (basic: 1,000/hr, premium: 5,000/hr, enterprise: 20,000/hr)
- **Core Endpoints**: Building inventory, summaries, industry benchmarks
- **Database Models**: `DataVendorAPIKey`, `DataVendorRequest` for tracking
- **NLP Foundation**: Existing NLP router with intent detection and slot filling
- **Admin Management**: API key management, usage analytics, CLI tools

### 🎯 **What We're Building**
- **Natural Language Interface**: Chat-based query processing with context management
- **Advanced Query Engine**: Complex filtering, cross-building queries, aggregation
- **Real-time Analytics**: Live data processing and predictive insights
- **Enterprise Security**: Data masking, audit logging, compliance features

---

## 🏗️ **System Architecture**

### **High-Level Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Vendor API Gateway                     │
├─────────────────────────────────────────────────────────────────┤
│  Authentication │ Rate Limiting │ Monitoring │ Security Headers │
├─────────────────────────────────────────────────────────────────┤
│                    Request Router                              │
├─────────────────┬─────────────────┬───────────────────────────┤
│   REST API      │   Chat API      │   WebSocket API          │
├─────────────────┴─────────────────┴───────────────────────────┤
│                    Service Layer                              │
├─────────────────┬─────────────────┬───────────────────────────┤
│  Query Engine   │  NLP Processor  │  Analytics Engine        │
├─────────────────┴─────────────────┴───────────────────────────┤
│                    Data Layer                                 │
├─────────────────┬─────────────────┬───────────────────────────┤
│  Building Data  │  Asset Data     │  Historical Data         │
└─────────────────┴─────────────────┴───────────────────────────┘
```

### **Core Components**

#### **1. API Gateway Layer**
- **Authentication**: JWT tokens + API keys for dual auth
- **Rate Limiting**: Advanced rate limiting with burst allowances
- **Monitoring**: Real-time metrics and performance tracking
- **Security**: CORS, audit logging, data masking

#### **2. Service Layer**
- **Query Engine**: Advanced filtering and aggregation
- **NLP Processor**: Natural language to query translation
- **Analytics Engine**: Real-time analytics and predictions
- **Session Manager**: Chat context and conversation state

#### **3. Data Layer**
- **Building Repository**: Multi-building data access
- **Asset Repository**: Comprehensive asset management
- **Historical Repository**: Time-series data and trends
- **Analytics Repository**: Pre-computed analytics data

---

## 🔧 **Implementation Strategy**

### **Phase 1: Natural Language Interface (Weeks 1-4)**
**Priority**: Critical
**Goal**: Enable conversational data access

#### **Week 1: Foundation Setup**

**Task 1.1: Extend NLP Router for Data Vendor Queries**
```python
# arxos/services/ai/arx-nlp/data_vendor_nlp_router.py
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from services.nlp_router import NLPRouter, NLPContext
from services.models.nlp_models import IntentType, SlotType

class DataVendorIntentType(IntentType):
    """Data vendor specific intent types"""
    QUERY_ASSETS = "query_assets"
    QUERY_BUILDINGS = "query_buildings"
    QUERY_ANALYTICS = "query_analytics"
    QUERY_HISTORY = "query_history"
    QUERY_MAINTENANCE = "query_maintenance"
    QUERY_PERFORMANCE = "query_performance"

class DataVendorNLPRouter(NLPRouter):
    """NLP Router specialized for data vendor queries"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._load_data_vendor_patterns()

    def _load_data_vendor_patterns(self):
        """Load data vendor specific NLP patterns"""
        self.data_vendor_patterns = {
            DataVendorIntentType.QUERY_ASSETS: [
                r'show\s+me\s+(\w+)',
                r'find\s+(\w+)',
                r'list\s+(\w+)',
                r'get\s+(\w+)',
                r'what\s+(\w+)'
            ],
            DataVendorIntentType.QUERY_BUILDINGS: [
                r'buildings?\s+with\s+(\w+)',
                r'buildings?\s+that\s+(\w+)',
                r'buildings?\s+in\s+(\w+)'
            ],
            DataVendorIntentType.QUERY_ANALYTICS: [
                r'analytics?\s+for\s+(\w+)',
                r'trends?\s+in\s+(\w+)',
                r'performance\s+of\s+(\w+)'
            ]
        }

    def parse_vendor_query(self, text: str, vendor_context: Dict) -> DataVendorResponse:
        """Parse data vendor specific queries"""
        # Create vendor-specific context
        context = NLPContext(
            user_id=vendor_context.get('vendor_id'),
            building_id=vendor_context.get('building_id'),
            permissions=vendor_context.get('permissions', []),
            object_context=vendor_context
        )

        # Parse with vendor patterns
        result = self.parse_natural_language(text, context)

        # Enhance with vendor-specific processing
        return DataVendorResponse(
            original_text=text,
            intent=result.intent,
            confidence=result.confidence,
            vendor_context=vendor_context,
            query_type=self._determine_query_type(result.intent),
            suggested_filters=self._extract_filters(text),
            timestamp=datetime.now()
        )
```

**Task 1.2: Create Chat Session Management**
```go
// arxos/core/backend/models/data_vendor_chat.go
package models

import (
    "time"
    "encoding/json"
)

type DataVendorChatSession struct {
    ID          string                 `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
    VendorID    uint                   `gorm:"not null;index" json:"vendor_id"`
    SessionID   string                 `gorm:"uniqueIndex;not null" json:"session_id"`
    Context     json.RawMessage        `gorm:"type:jsonb;default:'{}'" json:"context"`
    History     json.RawMessage        `gorm:"type:jsonb;default:'[]'" json:"history"`
    CreatedAt   time.Time              `json:"created_at"`
    UpdatedAt   time.Time              `json:"updated_at"`
    ExpiresAt   time.Time              `json:"expires_at"`
    IsActive    bool                   `gorm:"default:true" json:"is_active"`
}

type DataVendorChatMessage struct {
    ID          string                 `gorm:"primaryKey;type:uuid;default:gen_random_uuid()" json:"id"`
    SessionID   string                 `gorm:"not null;index" json:"session_id"`
    Role        string                 `gorm:"not null" json:"role"` // "user" or "assistant"
    Message     string                 `gorm:"type:text;not null" json:"message"`
    Metadata    json.RawMessage        `gorm:"type:jsonb;default:'{}'" json:"metadata"`
    CreatedAt   time.Time              `json:"created_at"`
}

type ChatRequest struct {
    Message     string                 `json:"message"`
    SessionID   string                 `json:"session_id,omitempty"`
    Context     map[string]interface{} `json:"context,omitempty"`
    VendorID    string                 `json:"vendor_id"`
}

type ChatResponse struct {
    Response    string                 `json:"response"`
    Data        interface{}            `json:"data,omitempty"`
    Confidence  float64                `json:"confidence"`
    SessionID   string                 `json:"session_id"`
    Suggestions []string               `json:"suggestions,omitempty"`
}
```

#### **Week 2: Query Translation Engine**

**Task 2.1: Query Translation Engine**
```python
class DataVendorQueryTranslator:
    """Translates natural language to structured queries"""

    def __init__(self):
        self.nlp_router = NLPRouter()
        self.query_builder = QueryBuilder()
        self.context_manager = ContextManager()

    def translate_query(self, message: str, context: Dict) -> QueryResult:
        """Translate natural language to database query"""
        # Parse intent and extract parameters
        nlp_result = self.nlp_router.parse_natural_language(message)

        # Build structured query
        query = self.query_builder.build_query(nlp_result, context)

        # Execute and format results
        results = self.execute_query(query)

        return QueryResult(
            data=results,
            confidence=nlp_result.confidence,
            query_type=query.type,
            metadata=query.metadata
        )
```

#### **Week 3-4: Chat API Endpoints**

**Task 3.1: Chat API Implementation**
```go
// arxos/core/backend/handlers/data_vendor_chat.go
package handlers

import (
    "net/http"
    "time"
    "github.com/gin-gonic/gin"
)

// POST /api/vendor/chat
func (h *DataVendorHandler) SendChatMessage(c *gin.Context) {
    var req ChatRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }

    // Validate vendor access
    vendorID := c.GetString("vendor_id")
    if !h.validateVendorAccess(vendorID, req.VendorID) {
        c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
        return
    }

    // Process chat message
    response, err := h.chatService.ProcessMessage(req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusOK, response)
}

// GET /api/vendor/chat/sessions
func (h *DataVendorHandler) ListChatSessions(c *gin.Context) {
    vendorID := c.GetString("vendor_id")
    sessions, err := h.chatService.ListSessions(vendorID)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusOK, sessions)
}
```

### **Phase 2: Advanced Query Engine (Weeks 5-8)**
**Priority**: High
**Goal**: Enable complex, cross-building queries

#### **Week 5-6: Query Builder Service**

**Task 5.1: Advanced Query Builder**
```go
type QueryBuilder struct {
    Filters     []Filter     `json:"filters"`
    Aggregations []Aggregation `json:"aggregations"`
    Sort        []Sort       `json:"sort"`
    Pagination  Pagination   `json:"pagination"`
    TimeRange   TimeRange    `json:"time_range,omitempty"`
}

type Filter struct {
    Field       string      `json:"field"`
    Operator    string      `json:"operator"` // eq, ne, gt, lt, in, contains
    Value       interface{} `json:"value"`
    LogicalOp   string      `json:"logical_op"` // and, or
}

type Aggregation struct {
    Type        string `json:"type"` // count, sum, avg, min, max
    Field       string `json:"field"`
    Alias       string `json:"alias,omitempty"`
}

type MultiBuildingQuery struct {
    Buildings   []string    `json:"buildings"` // Building IDs or "all"
    Query       QueryBuilder `json:"query"`
    GroupBy     []string    `json:"group_by,omitempty"`
    Compare     bool        `json:"compare,omitempty"` // Enable comparison mode
}
```

#### **Week 7-8: Cross-Building Query Support**

**Task 7.1: Cross-Building Query Implementation**
```python
class CrossBuildingQueryEngine:
    """Handle queries across multiple buildings"""

    def __init__(self):
        self.building_repository = BuildingRepository()
        self.asset_repository = AssetRepository()
        self.query_optimizer = QueryOptimizer()

    def execute_cross_building_query(self, query: MultiBuildingQuery) -> QueryResult:
        """Execute query across multiple buildings"""
        # Validate building access
        accessible_buildings = self.validate_building_access(query.buildings)

        # Optimize query for cross-building execution
        optimized_query = self.query_optimizer.optimize_for_cross_building(query)

        # Execute query across buildings
        results = []
        for building_id in accessible_buildings:
            building_result = self.execute_single_building_query(optimized_query, building_id)
            results.append(building_result)

        # Aggregate results
        aggregated_result = self.aggregate_cross_building_results(results, query)

        return QueryResult(
            data=aggregated_result.data,
            metadata=aggregated_result.metadata,
            analytics=aggregated_result.analytics
        )
```

### **Phase 3: Real-time & Analytics (Weeks 9-12)**
**Priority**: Medium
**Goal**: Enable real-time data and predictive analytics

#### **Week 9-10: WebSocket API**

**Task 9.1: WebSocket Implementation**
```go
type WebSocketMessage struct {
    Type        string                 `json:"type"`
    Channel     string                 `json:"channel"`
    Data        interface{}            `json:"data"`
    Timestamp   time.Time              `json:"timestamp"`
}

// Channels: building_updates, asset_changes, alerts, analytics
func (h *DataVendorHandler) HandleWebSocket(c *gin.Context) {
    vendorID := c.GetString("vendor_id")

    // Upgrade to WebSocket
    conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
    if err != nil {
        return
    }
    defer conn.Close()

    // Register connection
    h.wsManager.RegisterConnection(vendorID, conn)
    defer h.wsManager.UnregisterConnection(vendorID, conn)

    // Handle WebSocket messages
    for {
        var msg WebSocketMessage
        if err := conn.ReadJSON(&msg); err != nil {
            break
        }

        // Process message
        response := h.processWebSocketMessage(vendorID, msg)
        conn.WriteJSON(response)
    }
}
```

#### **Week 11-12: Analytics Engine**

**Task 11.1: Analytics Engine Implementation**
```python
class DataVendorAnalytics:
    """Real-time analytics for data vendors"""

    def __init__(self):
        self.trend_analyzer = TrendAnalyzer()
        self.predictor = PredictiveModel()
        self.anomaly_detector = AnomalyDetector()

    def generate_insights(self, data: Dict, query_context: Dict) -> AnalyticsResult:
        """Generate insights from query results"""
        insights = {
            "trends": self.trend_analyzer.analyze(data),
            "predictions": self.predictor.predict(data),
            "anomalies": self.anomaly_detector.detect(data),
            "recommendations": self.generate_recommendations(data)
        }

        return AnalyticsResult(
            insights=insights,
            confidence=self.calculate_confidence(insights),
            metadata=self.generate_metadata(data)
        )
```

### **Phase 4: Enterprise Features (Weeks 13-16)**
**Priority**: Low
**Goal**: Enterprise-grade security and compliance

#### **Week 13-14: Advanced Security**

**Task 13.1: Data Masking Implementation**
```go
type DataMaskingConfig struct {
    Fields       []string `json:"fields"`
    MaskType     string   `json:"mask_type"` // hash, partial, full
    AccessLevel  string   `json:"access_level"`
}

type AuditLog struct {
    ID          string                 `json:"id"`
    VendorID    string                 `json:"vendor_id"`
    Action      string                 `json:"action"`
    Resource    string                 `json:"resource"`
    Data        map[string]interface{} `json:"data"`
    Timestamp   time.Time              `json:"timestamp"`
    IPAddress   string                 `json:"ip_address"`
}
```

---

## 📊 **Success Metrics**

### **Phase 1 Success Criteria**
- [ ] Natural language queries processed with >80% accuracy
- [ ] Chat sessions maintain context across multiple messages
- [ ] Query translation generates valid database queries
- [ ] Response time < 2 seconds for typical queries

### **Phase 2 Success Criteria**
- [ ] Cross-building queries execute successfully
- [ ] Complex filters handle 10+ conditions
- [ ] Query optimization reduces response time by 50%
- [ ] Bulk queries process 1000+ records efficiently

### **Phase 3 Success Criteria**
- [ ] Real-time updates delivered within 1 second
- [ ] Predictive analytics achieve >70% accuracy
- [ ] Analytics insights generated in < 5 seconds
- [ ] WebSocket connections handle 1000+ concurrent users

### **Phase 4 Success Criteria**
- [ ] Data masking applied to sensitive fields
- [ ] Audit logs capture 100% of vendor activities
- [ ] Compliance features pass security audits
- [ ] Enterprise features support 100+ concurrent vendors

---

## 🔧 **Technical Specifications**

### **Database Schema Extensions**

```sql
-- Chat sessions for data vendors
CREATE TABLE data_vendor_chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID NOT NULL REFERENCES data_vendor_api_keys(id),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    context JSONB DEFAULT '{}',
    history JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Chat messages
CREATE TABLE data_vendor_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL REFERENCES data_vendor_chat_sessions(session_id),
    role VARCHAR(50) NOT NULL, -- 'user' or 'assistant'
    message TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query analytics
CREATE TABLE data_vendor_query_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor_id UUID NOT NULL REFERENCES data_vendor_api_keys(id),
    query_type VARCHAR(100) NOT NULL,
    query_text TEXT,
    result_count INTEGER,
    processing_time_ms INTEGER,
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **API Endpoints**

#### **New Chat Endpoints**
```
POST   /api/vendor/chat                    # Send chat message
GET    /api/vendor/chat/sessions           # List chat sessions
GET    /api/vendor/chat/sessions/{id}      # Get session details
DELETE /api/vendor/chat/sessions/{id}      # End session
```

#### **Enhanced Query Endpoints**
```
POST   /api/vendor/query                   # Advanced query endpoint
POST   /api/vendor/query/bulk             # Bulk query endpoint
GET    /api/vendor/query/templates        # Query templates
POST   /api/vendor/query/save             # Save query template
```

#### **Analytics Endpoints**
```
GET    /api/vendor/analytics/insights      # Get insights
GET    /api/vendor/analytics/trends        # Get trends
GET    /api/vendor/analytics/predictions   # Get predictions
POST   /api/vendor/analytics/custom        # Custom analytics
```

#### **Real-time Endpoints**
```
WS     /api/vendor/ws/updates             # WebSocket for real-time updates
GET    /api/vendor/stream/events          # Server-sent events
```

---

## 🚨 **Risk Mitigation**

### **Technical Risks**
1. **NLP Accuracy**: Implement fallback mechanisms and confidence thresholds
2. **Performance**: Use caching and query optimization
3. **Scalability**: Design for horizontal scaling from day one
4. **Security**: Comprehensive security testing and audit logging

### **Business Risks**
1. **User Adoption**: Provide comprehensive documentation and examples
2. **Data Quality**: Implement data validation and quality checks
3. **Compliance**: Regular compliance audits and updates
4. **Cost Management**: Monitor usage and implement cost controls

---

## 🎯 **Performance Requirements**

- **Response Time**: < 2 seconds for chat queries
- **Throughput**: 1000+ concurrent chat sessions
- **Availability**: 99.9% uptime
- **Scalability**: Horizontal scaling support
- **Caching**: Redis-based caching for frequent queries

### **Security Requirements**

- **Data Masking**: Configurable field-level masking
- **Audit Logging**: Comprehensive activity tracking
- **Rate Limiting**: Advanced rate limiting per session
- **Encryption**: AES-256 for data at rest and in transit
- **Compliance**: GDPR and HIPAA compliance features

---

## 🏆 **Conclusion**

This comprehensive Data Vendor API system will enable external data purchasers to query any object from any building in any quantity through both traditional API calls and natural language chat interfaces. By building upon existing infrastructure and leveraging established NLP capabilities, we can deliver a world-class data access platform that enables natural language queries, advanced analytics, and enterprise-grade security.

The phased approach ensures incremental value delivery while maintaining system stability and performance. Each phase builds upon the previous one, creating a robust foundation for the next level of functionality.

---

**Implementation Date**: December 2024
**Version**: 1.0.0
**Status**: In Development
