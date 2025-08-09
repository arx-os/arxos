"""
AI Integration API for SVGX Engine

This module provides FastAPI endpoints for AI integration services including:
- User pattern learning and behavior tracking
- HTMX-powered AI frontend integration
- Advanced AI analytics and insights
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from svgx_engine.services.ai.user_pattern_learning import (
    UserPatternLearningService,
    UserActionType,
    UserContext,
    PatternType
)
from svgx_engine.services.ai.ai_frontend_integration import (
    AIFrontendIntegrationService,
    HTMXEventType,
    AIComponentType
)
from svgx_engine.services.ai.advanced_ai_analytics import (
    AdvancedAIAnalyticsService,
    AnalyticsType,
    PredictionModel,
    InsightType
)
from core.security.auth_middleware import get_current_user, User

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Integration API",
    description="API for AI integration services including user pattern learning, HTMX frontend integration, and advanced analytics",
    version="1.0.0"
)

# Initialize services
user_pattern_service = UserPatternLearningService()
ai_frontend_service = AIFrontendIntegrationService()
ai_analytics_service = AdvancedAIAnalyticsService()


# Data Models for API
class UserActionRequest(BaseModel):
    """Request model for recording user action"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    action_type: str = Field(..., description="Type of action")
    context: str = Field(..., description="User context")
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    duration: Optional[float] = None
    success: bool = Field(default=True)
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[List[float]] = None


class UserSessionRequest(BaseModel):
    """Request model for user session"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    location: Optional[List[float]] = None
    device_info: Dict[str, Any] = Field(default_factory=dict)


class HTMXRequestModel(BaseModel):
    """Request model for HTMX interactions"""
    user_id: str = Field(..., description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    event_type: str = Field(..., description="Type of HTMX event")
    target_id: str = Field(..., description="Target element ID")
    component_type: str = Field(..., description="AI component type")
    request_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class PredictionRequest(BaseModel):
    """Request model for predictions"""
    user_id: str = Field(..., description="User identifier")
    target_variable: str = Field(..., description="Target variable for prediction")
    model_type: str = Field(default="linear_regression", description="Type of prediction model")
    prediction_horizon: int = Field(default=30, description="Prediction horizon in days")


class AnalyticsRequest(BaseModel):
    """Request model for analytics"""
    dataset_name: str = Field(..., description="Dataset name")
    description: str = Field(..., description="Dataset description")
    data_type: str = Field(..., description="Type of data")
    data_points: List[Dict[str, Any]] = Field(..., description="Data points")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InsightRequest(BaseModel):
    """Request model for insights"""
    user_id: str = Field(..., description="User identifier")
    insight_types: List[str] = Field(default_factory=list, description="Types of insights to generate")


# User Pattern Learning Endpoints
@app.post("/user-actions", response_model=Dict)
async def record_user_action(request: UserActionRequest, user: User = Depends(get_current_user)):
    """Record a user action for pattern learning"""
    try:
        # Convert location to tuple if provided
        location_tuple = tuple(request.location) if request.location else None

        action = await user_pattern_service.record_user_action(
            user_id=request.user_id,
            session_id=request.session_id,
            action_type=UserActionType(request.action_type),
            context=UserContext(request.context),
            resource_id=request.resource_id,
            resource_type=request.resource_type,
            metadata=request.metadata,
            duration=request.duration,
            success=request.success,
            error_message=request.error_message,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            location=location_tuple
        )

        return {
            "success": True,
            "action_id": str(action.id),
            "message": "User action recorded successfully"
        }
    except Exception as e:
        logger.error(f"Failed to record user action: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/user-sessions/start", response_model=Dict)
async def start_user_session(request: UserSessionRequest, user: User = Depends(get_current_user)):
    """Start a new user session"""
    try:
        # Convert location to tuple if provided
        location_tuple = tuple(request.location) if request.location else None

        session = await user_pattern_service.start_user_session(
            user_id=request.user_id,
            session_id=request.session_id,
            ip_address=request.ip_address,
            user_agent=request.user_agent,
            location=location_tuple,
            device_info=request.device_info
        )

        return {
            "success": True,
            "session_id": session.id,
            "message": "User session started successfully"
        }
    except Exception as e:
        logger.error(f"Failed to start user session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/user-sessions/{session_id}/end", response_model=Dict)
async def end_user_session(session_id: str, user: User = Depends(get_current_user)):
    """End a user session"""
    try:
        session = await user_pattern_service.end_user_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "session_duration": session.duration,
            "message": "User session ended successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end user session: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/user-patterns/{user_id}", response_model=Dict)
async def get_user_patterns(
    user_id: str,
    pattern_type: Optional[str] = None,
    context: Optional[str] = None,
    active_only: bool = True,
    user: User = Depends(get_current_user)):
    """Get user patterns"""
    try:
        pattern_type_enum = PatternType(pattern_type) if pattern_type else None
        context_enum = UserContext(context) if context else None

        patterns = await user_pattern_service.get_user_patterns(
            user_id=user_id,
            pattern_type=pattern_type_enum,
            context=context_enum,
            active_only=active_only
        )

        return {
            "success": True,
            "patterns": [p.dict() for p in patterns],
            "count": len(patterns)
        }
    except Exception as e:
        logger.error(f"Failed to get user patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/user-recommendations/{user_id}", response_model=Dict)
async def get_user_recommendations(
    user_id: str,
    recommendation_type: Optional[str] = None,
    active_only: bool = True,
    user: User = Depends(get_current_user)):
    """Get user recommendations"""
    try:
        recommendations = await user_pattern_service.get_user_recommendations(
            user_id=user_id,
            recommendation_type=recommendation_type,
            active_only=active_only
        )

        return {
            "success": True,
            "recommendations": [r.dict() for r in recommendations],
            "count": len(recommendations)
        }
    except Exception as e:
        logger.error(f"Failed to get user recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/user-analytics/{user_id}", response_model=Dict)
async def get_user_analytics(user_id: str, user: User = Depends(get_current_user)):
    """Get user analytics"""
    try:
        analytics = await user_pattern_service.get_user_analytics(user_id)
        if not analytics:
            raise HTTPException(status_code=404, detail="User analytics not found")

        return {
            "success": True,
            "analytics": analytics.dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/user-insights/{user_id}", response_model=Dict)
async def get_user_insights(user_id: str, user: User = Depends(get_current_user)):
    """Get comprehensive user insights"""
    try:
        insights = await user_pattern_service.get_user_insights(user_id)

        return {
            "success": True,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Failed to get user insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# HTMX AI Frontend Integration Endpoints
@app.post("/htmx/process", response_model=Dict)
async def process_htmx_request(request: HTMXRequestModel, user: User = Depends(get_current_user)):
    """Process HTMX request and generate AI-powered response"""
    try:
        # Convert location to tuple if provided
        location_tuple = tuple(request.context.get("location", [])) if request.context.get("location") else None

        response = await ai_frontend_service.process_htmx_request(
            user_id=request.user_id,
            session_id=request.session_id,
            event_type=HTMXEventType(request.event_type),
            target_id=request.target_id,
            component_type=AIComponentType(request.component_type),
            request_data=request.request_data,
            context=request.context,
            ip_address=request.ip_address,
            user_agent=request.user_agent
        )

        return {
            "success": True,
            "response_id": str(response.id),
            "html_content": response.html_content,
            "htmx_attributes": response.htmx_attributes,
            "metadata": response.metadata,
            "processing_time": response.processing_time
        }
    except Exception as e:
        logger.error(f"Failed to process HTMX request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/ai-components", response_model=Dict)
async def create_ai_component(
    component_type: str,
    name: str,
    description: str,
    target_selector: str,
    htmx_config: Dict[str, Any] = None,
    ai_config: Dict[str, Any] = None,
    user: User = Depends(get_current_user)):
    """Create a new AI component"""
    try:
        component = await ai_frontend_service.create_ai_component(
            component_type=AIComponentType(component_type),
            name=name,
            description=description,
            target_selector=target_selector,
            htmx_config=htmx_config or {},
            ai_config=ai_config or {}
        )

        return {
            "success": True,
            "component_id": str(component.id),
            "message": "AI component created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create AI component: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/ai-components", response_model=Dict)
async def get_ai_components(
    component_type: Optional[str] = None,
    active_only: bool = True,
    user: User = Depends(get_current_user)):
    """Get AI components"""
    try:
        component_type_enum = AIComponentType(component_type) if component_type else None

        components = await ai_frontend_service.get_ai_components(
            component_type=component_type_enum,
            active_only=active_only
        )

        return {
            "success": True,
            "components": [c.dict() for c in components],
            "count": len(components)
        }
    except Exception as e:
        logger.error(f"Failed to get AI components: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# Advanced AI Analytics Endpoints
@app.post("/predictions", response_model=Dict)
async def generate_prediction(request: PredictionRequest, user: User = Depends(get_current_user)):
    """Generate prediction using AI models"""
    try:
        prediction = await ai_analytics_service.predict_user_behavior(
            user_id=request.user_id,
            target_variable=request.target_variable,
            model_type=PredictionModel(request.model_type),
            prediction_horizon=request.prediction_horizon
        )

        return {
            "success": True,
            "prediction": prediction.dict(),
            "message": "Prediction generated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to generate prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/analytics/datasets", response_model=Dict)
async def create_analytics_dataset(request: AnalyticsRequest, user: User = Depends(get_current_user)):
    """Create analytics dataset"""
    try:
        dataset = await ai_analytics_service.create_dataset(
            name=request.dataset_name,
            description=request.description,
            data_type=request.data_type,
            data_points=request.data_points,
            metadata=request.metadata
        )

        return {
            "success": True,
            "dataset_id": str(dataset.id),
            "message": "Analytics dataset created successfully"
        }
    except Exception as e:
        logger.error(f"Failed to create analytics dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/analytics/trends/{dataset_id}", response_model=Dict)
async def analyze_trends(dataset_id: UUID, variable_name: str, user: User = Depends(get_current_user)):
    """Analyze trends in dataset"""
    try:
        trend = await ai_analytics_service.analyze_trends(
            dataset_id=dataset_id,
            variable_name=variable_name
        )

        return {
            "success": True,
            "trend": trend.dict(),
            "message": "Trend analysis completed successfully"
        }
    except Exception as e:
        logger.error(f"Failed to analyze trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/analytics/correlations/{dataset_id}", response_model=Dict)
async def analyze_correlations(
    dataset_id: UUID,
    variable1: str,
    variable2: str,
    user: User = Depends(get_current_user)):
    """Analyze correlations between variables"""
    try:
        correlation = await ai_analytics_service.analyze_correlations(
            dataset_id=dataset_id,
            variable1=variable1,
            variable2=variable2
        )

        return {
            "success": True,
            "correlation": correlation.dict(),
            "message": "Correlation analysis completed successfully"
        }
    except Exception as e:
        logger.error(f"Failed to analyze correlations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/analytics/anomalies/{dataset_id}", response_model=Dict)
async def detect_anomalies(
    dataset_id: UUID,
    variable_name: str,
    threshold: float = 2.0,
    user: User = Depends(get_current_user)):
    """Detect anomalies in dataset"""
    try:
        anomalies = await ai_analytics_service.detect_anomalies(
            dataset_id=dataset_id,
            variable_name=variable_name,
            threshold=threshold
        )

        return {
            "success": True,
            "anomalies": [a.dict() for a in anomalies],
            "count": len(anomalies),
            "message": "Anomaly detection completed successfully"
        }
    except Exception as e:
        logger.error(f"Failed to detect anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/analytics/insights", response_model=Dict)
async def generate_insights(request: InsightRequest, user: User = Depends(get_current_user)):
    """Generate AI insights"""
    try:
        insight_types = [InsightType(it) for it in request.insight_types] if request.insight_types else None

        insights = await ai_analytics_service.generate_insights(
            user_id=request.user_id,
            insight_types=insight_types
        )

        return {
            "success": True,
            "insights": [i.dict() for i in insights],
            "count": len(insights),
            "message": "Insights generated successfully"
        }
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/analytics/metrics", response_model=Dict)
async def track_performance_metrics(
    metric_name: str,
    metric_value: float,
    unit: str,
    benchmark: Optional[float] = None,
    target: Optional[float] = None,
    user: User = Depends(get_current_user)):
    """Track performance metrics"""
    try:
        metric = await ai_analytics_service.track_performance_metrics(
            metric_name=metric_name,
            metric_value=metric_value,
            unit=unit,
            benchmark=benchmark,
            target=target
        )

        return {
            "success": True,
            "metric": metric.dict(),
            "message": "Performance metric tracked successfully"
        }
    except Exception as e:
        logger.error(f"Failed to track performance metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.get("/analytics/summary/{user_id}", response_model=Dict)
async def get_analytics_summary(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user: User = Depends(get_current_user)):
    """Get comprehensive analytics summary"""
    try:
        summary = await ai_analytics_service.get_analytics_summary(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )

        return {
            "success": True,
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Failed to get analytics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# Recommendation Management Endpoints
@app.post("/recommendations/{recommendation_id}/dismiss", response_model=Dict)
async def dismiss_recommendation(recommendation_id: UUID, user: User = Depends(get_current_user)):
    """Dismiss a user recommendation"""
    try:
        success = await user_pattern_service.dismiss_recommendation(recommendation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        return {
            "success": True,
            "message": "Recommendation dismissed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to dismiss recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@app.post("/recommendations/{recommendation_id}/apply", response_model=Dict)
async def apply_recommendation(recommendation_id: UUID, user: User = Depends(get_current_user)):
    """Apply a user recommendation"""
    try:
        success = await user_pattern_service.apply_recommendation(recommendation_id)
        if not success:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        return {
            "success": True,
            "message": "Recommendation applied successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# Health check endpoint
@app.get("/health", response_model=Dict)
async def health_check(user: User = Depends(get_current_user)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Integration API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
