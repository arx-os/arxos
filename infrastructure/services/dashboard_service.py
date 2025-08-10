"""
Dashboard Management Service.

Advanced dashboard service for creating, managing, and serving
monitoring dashboards with real-time data visualization.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
import uuid
from collections import defaultdict

from domain.entities.monitoring_entity import (
    Dashboard, DashboardType, Metric, Alert, AlertSeverity, AlertStatus
)
from infrastructure.logging.structured_logging import get_logger, log_context
from infrastructure.performance.monitoring import performance_monitor


logger = get_logger(__name__)


class DashboardService:
    """Advanced dashboard management service."""
    
    def __init__(self, monitoring_service=None):
        self.monitoring_service = monitoring_service
        
        # Dashboard storage
        self.dashboards: Dict[str, Dashboard] = {}
        self.dashboard_templates: Dict[str, Dict[str, Any]] = {}
        
        # Real-time data caching
        self.data_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Widget type handlers
        self.widget_handlers: Dict[str, Callable] = {
            "metric_chart": self._handle_metric_chart,
            "metric_value": self._handle_metric_value,
            "alert_summary": self._handle_alert_summary,
            "system_status": self._handle_system_status,
            "performance_gauge": self._handle_performance_gauge,
            "log_stream": self._handle_log_stream,
            "service_map": self._handle_service_map,
            "heatmap": self._handle_heatmap,
            "table": self._handle_table,
            "text": self._handle_text
        }
        
        # Built-in dashboard templates
        self._initialize_dashboard_templates()
        
        # Statistics
        self.service_stats = {
            "total_dashboards": 0,
            "active_dashboards": 0,
            "total_widgets": 0,
            "data_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def _initialize_dashboard_templates(self) -> None:
        """Initialize built-in dashboard templates."""
        self.dashboard_templates = {
            "system_overview": {
                "name": "System Overview",
                "description": "Comprehensive system health and performance overview",
                "dashboard_type": DashboardType.SYSTEM_HEALTH.value,
                "widgets": [
                    {
                        "type": "system_status",
                        "title": "System Status",
                        "position": {"x": 0, "y": 0, "width": 6, "height": 3},
                        "config": {"show_uptime": True, "show_alerts": True}
                    },
                    {
                        "type": "metric_chart",
                        "title": "CPU Usage",
                        "position": {"x": 6, "y": 0, "width": 6, "height": 3},
                        "config": {
                            "metric_name": "system.cpu.usage",
                            "chart_type": "line",
                            "time_range": {"last": "1h"}
                        }
                    },
                    {
                        "type": "metric_chart",
                        "title": "Memory Usage",
                        "position": {"x": 0, "y": 3, "width": 6, "height": 3},
                        "config": {
                            "metric_name": "system.memory.usage",
                            "chart_type": "line",
                            "time_range": {"last": "1h"}
                        }
                    },
                    {
                        "type": "alert_summary",
                        "title": "Active Alerts",
                        "position": {"x": 6, "y": 3, "width": 6, "height": 3},
                        "config": {"show_severity_breakdown": True}
                    }
                ],
                "layout": {"grid_size": 12},
                "time_range": {"last": "1h"},
                "refresh_interval_seconds": 30
            },
            "application_performance": {
                "name": "Application Performance",
                "description": "Application performance metrics and monitoring",
                "dashboard_type": DashboardType.PERFORMANCE.value,
                "widgets": [
                    {
                        "type": "metric_value",
                        "title": "Response Time",
                        "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                        "config": {
                            "metric_name": "application.response.time",
                            "unit": "ms",
                            "show_trend": True
                        }
                    },
                    {
                        "type": "metric_value",
                        "title": "Requests/sec",
                        "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                        "config": {
                            "metric_name": "application.requests.rate",
                            "unit": "req/s",
                            "show_trend": True
                        }
                    },
                    {
                        "type": "metric_value",
                        "title": "Error Rate",
                        "position": {"x": 6, "y": 0, "width": 3, "height": 2},
                        "config": {
                            "metric_name": "application.error.rate",
                            "unit": "%",
                            "show_trend": True
                        }
                    },
                    {
                        "type": "performance_gauge",
                        "title": "Overall Health",
                        "position": {"x": 9, "y": 0, "width": 3, "height": 2},
                        "config": {
                            "metrics": [
                                "application.response.time",
                                "application.error.rate",
                                "application.availability"
                            ]
                        }
                    },
                    {
                        "type": "metric_chart",
                        "title": "Response Time Trend",
                        "position": {"x": 0, "y": 2, "width": 12, "height": 4},
                        "config": {
                            "metric_name": "application.response.time",
                            "chart_type": "line",
                            "time_range": {"last": "6h"}
                        }
                    }
                ],
                "time_range": {"last": "1h"},
                "refresh_interval_seconds": 30
            },
            "security_dashboard": {
                "name": "Security Monitoring",
                "description": "Security events and threat monitoring",
                "dashboard_type": DashboardType.SECURITY.value,
                "widgets": [
                    {
                        "type": "metric_value",
                        "title": "Failed Logins",
                        "position": {"x": 0, "y": 0, "width": 3, "height": 2},
                        "config": {
                            "metric_name": "security.failed_logins.count",
                            "unit": "count",
                            "show_trend": True
                        }
                    },
                    {
                        "type": "metric_value",
                        "title": "Blocked IPs",
                        "position": {"x": 3, "y": 0, "width": 3, "height": 2},
                        "config": {
                            "metric_name": "security.blocked_ips.count",
                            "unit": "count",
                            "show_trend": True
                        }
                    },
                    {
                        "type": "alert_summary",
                        "title": "Security Alerts",
                        "position": {"x": 6, "y": 0, "width": 6, "height": 2},
                        "config": {
                            "filter": {"category": "security"},
                            "show_severity_breakdown": True
                        }
                    },
                    {
                        "type": "heatmap",
                        "title": "Attack Sources",
                        "position": {"x": 0, "y": 2, "width": 12, "height": 4},
                        "config": {
                            "metric_name": "security.attack_sources",
                            "dimension": "source_ip"
                        }
                    }
                ],
                "time_range": {"last": "24h"},
                "refresh_interval_seconds": 60
            },
            "business_metrics": {
                "name": "Business Metrics",
                "description": "Key business performance indicators",
                "dashboard_type": DashboardType.BUSINESS_METRICS.value,
                "widgets": [
                    {
                        "type": "metric_value",
                        "title": "Revenue",
                        "position": {"x": 0, "y": 0, "width": 4, "height": 3},
                        "config": {
                            "metric_name": "business.revenue.total",
                            "unit": "$",
                            "show_trend": True,
                            "format": "currency"
                        }
                    },
                    {
                        "type": "metric_value",
                        "title": "Active Users",
                        "position": {"x": 4, "y": 0, "width": 4, "height": 3},
                        "config": {
                            "metric_name": "business.active_users.count",
                            "unit": "users",
                            "show_trend": True
                        }
                    },
                    {
                        "type": "metric_value",
                        "title": "Conversion Rate",
                        "position": {"x": 8, "y": 0, "width": 4, "height": 3},
                        "config": {
                            "metric_name": "business.conversion.rate",
                            "unit": "%",
                            "show_trend": True
                        }
                    },
                    {
                        "type": "metric_chart",
                        "title": "Revenue Trend",
                        "position": {"x": 0, "y": 3, "width": 12, "height": 4},
                        "config": {
                            "metric_name": "business.revenue.total",
                            "chart_type": "area",
                            "time_range": {"last": "7d"}
                        }
                    }
                ],
                "time_range": {"last": "24h"},
                "refresh_interval_seconds": 300
            }
        }

    def create_dashboard(self, dashboard_data: Dict[str, Any], created_by: str) -> Dashboard:
        """Create new dashboard."""
        with log_context(operation="create_dashboard", user=created_by):
            try:
                dashboard = Dashboard(
                    name=dashboard_data["name"],
                    description=dashboard_data.get("description", ""),
                    dashboard_type=DashboardType(dashboard_data.get("dashboard_type", "custom")),
                    widgets=dashboard_data.get("widgets", []),
                    layout=dashboard_data.get("layout", {}),
                    visibility=dashboard_data.get("visibility", "private"),
                    owner=created_by,
                    shared_with=dashboard_data.get("shared_with", []),
                    refresh_interval_seconds=dashboard_data.get("refresh_interval_seconds", 300),
                    auto_refresh=dashboard_data.get("auto_refresh", True),
                    time_range=dashboard_data.get("time_range", {"last": "1h"}),
                    tags=dashboard_data.get("tags", {})
                )
                
                # Store dashboard
                self.dashboards[dashboard.id] = dashboard
                self.service_stats["total_dashboards"] += 1
                self.service_stats["total_widgets"] += len(dashboard.widgets)
                
                logger.info(f"Created dashboard: {dashboard.name}")
                
                return dashboard
                
            except Exception as e:
                logger.error(f"Failed to create dashboard: {e}")
                raise

    def create_dashboard_from_template(self, template_id: str, 
                                     customizations: Dict[str, Any],
                                     created_by: str) -> Dashboard:
        """Create dashboard from template."""
        if template_id not in self.dashboard_templates:
            raise ValueError(f"Template not found: {template_id}")
        
        template = self.dashboard_templates[template_id].copy()
        
        # Apply customizations
        if "name" in customizations:
            template["name"] = customizations["name"]
        
        if "time_range" in customizations:
            template["time_range"] = customizations["time_range"]
        
        if "refresh_interval_seconds" in customizations:
            template["refresh_interval_seconds"] = customizations["refresh_interval_seconds"]
        
        # Customize widget configurations
        if "widget_customizations" in customizations:
            for widget_id, widget_customizations in customizations["widget_customizations"].items():
                for widget in template["widgets"]:
                    if widget.get("id") == widget_id:
                        widget["config"].update(widget_customizations)
        
        return self.create_dashboard(template, created_by)

    def update_dashboard(self, dashboard_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing dashboard."""
        if dashboard_id not in self.dashboards:
            return False
        
        dashboard = self.dashboards[dashboard_id]
        
        # Update fields
        for field, value in updates.items():
            if hasattr(dashboard, field):
                setattr(dashboard, field, value)
        
        dashboard.updated_at = datetime.now(timezone.utc)
        
        # Update widget count
        if "widgets" in updates:
            old_widget_count = len(dashboard.widgets)
            new_widget_count = len(updates["widgets"])
            self.service_stats["total_widgets"] += (new_widget_count - old_widget_count)
        
        # Clear cache for this dashboard
        self._clear_dashboard_cache(dashboard_id)
        
        logger.info(f"Updated dashboard: {dashboard.name}")
        return True

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete dashboard."""
        if dashboard_id not in self.dashboards:
            return False
        
        dashboard = self.dashboards[dashboard_id]
        
        # Remove from storage
        del self.dashboards[dashboard_id]
        self.service_stats["total_dashboards"] -= 1
        self.service_stats["total_widgets"] -= len(dashboard.widgets)
        
        # Clear cache
        self._clear_dashboard_cache(dashboard_id)
        
        logger.info(f"Deleted dashboard: {dashboard.name}")
        return True

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get dashboard by ID."""
        return self.dashboards.get(dashboard_id)

    def list_dashboards(self, owner: Optional[str] = None,
                       dashboard_type: Optional[DashboardType] = None,
                       tags: Optional[Dict[str, str]] = None) -> List[Dashboard]:
        """List dashboards with optional filtering."""
        dashboards = list(self.dashboards.values())
        
        # Apply filters
        if owner:
            dashboards = [d for d in dashboards if d.owner == owner]
        
        if dashboard_type:
            dashboards = [d for d in dashboards if d.dashboard_type == dashboard_type]
        
        if tags:
            dashboards = [d for d in dashboards if all(
                d.tags.get(k) == v for k, v in tags.items()
            )]
        
        return sorted(dashboards, key=lambda x: x.updated_at, reverse=True)

    @performance_monitor("get_dashboard_data")
    async def get_dashboard_data(self, dashboard_id: str, 
                               time_range: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get real-time dashboard data."""
        if dashboard_id not in self.dashboards:
            raise ValueError("Dashboard not found")
        
        dashboard = self.dashboards[dashboard_id]
        
        # Use provided time range or dashboard default
        effective_time_range = time_range or dashboard.time_range
        
        # Check cache
        cache_key = f"{dashboard_id}_{json.dumps(effective_time_range, sort_keys=True)}"
        
        if self._is_cache_valid(cache_key):
            self.service_stats["cache_hits"] += 1
            return self.data_cache[cache_key]
        
        self.service_stats["cache_misses"] += 1
        self.service_stats["data_requests"] += 1
        
        # Generate widget data
        widget_data = {}
        
        for widget in dashboard.widgets:
            widget_id = widget.get("id", str(uuid.uuid4()))
            widget_type = widget["type"]
            widget_config = widget.get("config", {})
            
            # Override time range if provided
            if effective_time_range != dashboard.time_range:
                widget_config = widget_config.copy()
                widget_config["time_range"] = effective_time_range
            
            try:
                if widget_type in self.widget_handlers:
                    widget_data[widget_id] = await self.widget_handlers[widget_type](widget_config)
                else:
                    widget_data[widget_id] = {"error": f"Unknown widget type: {widget_type}"}
                    
            except Exception as e:
                logger.error(f"Failed to get data for widget {widget_id}: {e}")
                widget_data[widget_id] = {"error": str(e)}
        
        # Prepare dashboard data
        dashboard_data = {
            "dashboard_id": dashboard_id,
            "name": dashboard.name,
            "updated_at": dashboard.updated_at.isoformat(),
            "time_range": effective_time_range,
            "auto_refresh": dashboard.auto_refresh,
            "refresh_interval_seconds": dashboard.refresh_interval_seconds,
            "widget_data": widget_data,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache the data
        self.data_cache[cache_key] = dashboard_data
        self.cache_timestamps[cache_key] = datetime.now(timezone.utc)
        
        # Record view
        dashboard.record_view()
        
        return dashboard_data

    async def _handle_metric_chart(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle metric chart widget."""
        metric_name = config.get("metric_name")
        if not metric_name or not self.monitoring_service:
            return {"error": "Metric name required and monitoring service must be available"}
        
        # Get time range
        time_range = config.get("time_range", {"last": "1h"})
        
        # Calculate actual time range
        end_time = datetime.now(timezone.utc)
        if "last" in time_range:
            duration = time_range["last"]
            if duration.endswith("h"):
                hours = int(duration[:-1])
                start_time = end_time - timedelta(hours=hours)
            elif duration.endswith("m"):
                minutes = int(duration[:-1])
                start_time = end_time - timedelta(minutes=minutes)
            elif duration.endswith("d"):
                days = int(duration[:-1])
                start_time = end_time - timedelta(days=days)
            else:
                start_time = end_time - timedelta(hours=1)
        else:
            start_time = end_time - timedelta(hours=1)
        
        # Get metric data (simulated for now)
        chart_data = {
            "labels": [],
            "values": [],
            "metric_name": metric_name,
            "chart_type": config.get("chart_type", "line"),
            "unit": "",
            "data_points": 0
        }
        
        # Simulate data points
        current_time = start_time
        while current_time <= end_time:
            chart_data["labels"].append(current_time.isoformat())
            # Simulate metric value
            import random
            chart_data["values"].append(random.uniform(10, 90))
            current_time += timedelta(minutes=5)
        
        chart_data["data_points"] = len(chart_data["values"])
        
        return chart_data

    async def _handle_metric_value(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle single metric value widget."""
        metric_name = config.get("metric_name")
        if not metric_name:
            return {"error": "Metric name required"}
        
        # Simulate current value
        import random
        current_value = random.uniform(10, 90)
        
        # Simulate trend
        trend = random.choice(["up", "down", "stable"])
        
        return {
            "value": current_value,
            "unit": config.get("unit", ""),
            "trend": trend if config.get("show_trend", False) else None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "format": config.get("format", "number")
        }

    async def _handle_alert_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle alert summary widget."""
        # Simulate alert data
        severity_breakdown = {
            "critical": 2,
            "high": 5,
            "medium": 12,
            "low": 8
        }
        
        total_active = sum(severity_breakdown.values())
        
        # Simulate recent alerts
        recent_alerts = []
        for i in range(5):
            recent_alerts.append({
                "id": str(uuid.uuid4()),
                "rule_name": f"Sample Alert {i+1}",
                "severity": ["critical", "high", "medium", "low"][i % 4],
                "triggered_at": (datetime.now(timezone.utc) - timedelta(minutes=i*10)).isoformat(),
                "status": "active"
            })
        
        return {
            "active_alerts": total_active,
            "severity_breakdown": severity_breakdown,
            "recent_alerts": recent_alerts,
            "show_severity_breakdown": config.get("show_severity_breakdown", True)
        }

    async def _handle_system_status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system status widget."""
        return {
            "status": "healthy",
            "uptime": 86400,  # 24 hours in seconds
            "services": {
                "api": "healthy",
                "database": "healthy", 
                "cache": "warning",
                "monitoring": "healthy"
            },
            "resource_usage": {
                "cpu": 45.2,
                "memory": 67.8,
                "disk": 34.1
            },
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "show_uptime": config.get("show_uptime", True),
            "show_alerts": config.get("show_alerts", True)
        }

    async def _handle_performance_gauge(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle performance gauge widget."""
        metrics = config.get("metrics", [])
        
        # Simulate performance score
        import random
        score = random.uniform(75, 95)
        
        # Determine status based on score
        if score >= 90:
            status = "excellent"
        elif score >= 80:
            status = "good"
        elif score >= 70:
            status = "warning"
        else:
            status = "critical"
        
        return {
            "score": round(score, 1),
            "status": status,
            "metrics": metrics,
            "breakdown": {
                "response_time": random.uniform(80, 95),
                "error_rate": random.uniform(85, 99),
                "availability": random.uniform(95, 100)
            },
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _handle_log_stream(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle log stream widget."""
        # Simulate log entries
        log_entries = []
        
        for i in range(10):
            log_entries.append({
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=i)).isoformat(),
                "level": ["INFO", "WARNING", "ERROR", "DEBUG"][i % 4],
                "message": f"Sample log message {i+1}",
                "source": f"service-{(i % 3) + 1}"
            })
        
        return {
            "entries": log_entries,
            "total_entries": len(log_entries),
            "log_source": config.get("log_source", "all"),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _handle_service_map(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service map widget."""
        # Simulate service topology
        services = [
            {"id": "api", "name": "API Gateway", "status": "healthy", "connections": ["auth", "db"]},
            {"id": "auth", "name": "Auth Service", "status": "healthy", "connections": ["db"]},
            {"id": "db", "name": "Database", "status": "warning", "connections": []},
            {"id": "cache", "name": "Redis Cache", "status": "healthy", "connections": []}
        ]
        
        return {
            "services": services,
            "connections": [
                {"from": "api", "to": "auth", "status": "healthy"},
                {"from": "api", "to": "db", "status": "healthy"},
                {"from": "auth", "to": "db", "status": "warning"}
            ],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _handle_heatmap(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle heatmap widget."""
        # Simulate heatmap data
        import random
        
        heatmap_data = []
        for x in range(24):  # 24 hours
            for y in range(7):  # 7 days
                heatmap_data.append({
                    "x": x,
                    "y": y,
                    "value": random.randint(0, 100)
                })
        
        return {
            "data": heatmap_data,
            "x_labels": [f"{i:02d}:00" for i in range(24)],
            "y_labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "metric_name": config.get("metric_name", ""),
            "dimension": config.get("dimension", ""),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _handle_table(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle table widget."""
        # Simulate table data
        columns = config.get("columns", ["Name", "Status", "Value", "Last Updated"])
        
        rows = []
        for i in range(10):
            rows.append([
                f"Item {i+1}",
                ["Active", "Inactive", "Warning"][i % 3],
                f"{(i+1) * 10}%",
                (datetime.now(timezone.utc) - timedelta(minutes=i)).strftime("%H:%M:%S")
            ])
        
        return {
            "columns": columns,
            "rows": rows,
            "total_rows": len(rows),
            "sortable": config.get("sortable", True),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    async def _handle_text(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text widget."""
        return {
            "content": config.get("content", ""),
            "format": config.get("format", "plain"),  # plain, markdown, html
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    def _is_cache_valid(self, cache_key: str, max_age_seconds: int = 60) -> bool:
        """Check if cache entry is valid."""
        if cache_key not in self.data_cache:
            return False
        
        cache_time = self.cache_timestamps.get(cache_key)
        if not cache_time:
            return False
        
        age_seconds = (datetime.now(timezone.utc) - cache_time).total_seconds()
        return age_seconds < max_age_seconds

    def _clear_dashboard_cache(self, dashboard_id: str) -> None:
        """Clear cache entries for dashboard."""
        keys_to_remove = [k for k in self.data_cache.keys() if k.startswith(dashboard_id)]
        
        for key in keys_to_remove:
            if key in self.data_cache:
                del self.data_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]

    def get_dashboard_templates(self) -> List[Dict[str, Any]]:
        """Get available dashboard templates."""
        templates = []
        
        for template_id, template_data in self.dashboard_templates.items():
            templates.append({
                "id": template_id,
                "name": template_data["name"],
                "description": template_data["description"],
                "dashboard_type": template_data["dashboard_type"],
                "widget_count": len(template_data["widgets"])
            })
        
        return templates

    def export_dashboard(self, dashboard_id: str) -> Dict[str, Any]:
        """Export dashboard configuration."""
        if dashboard_id not in self.dashboards:
            raise ValueError("Dashboard not found")
        
        dashboard = self.dashboards[dashboard_id]
        
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "dashboard": {
                "name": dashboard.name,
                "description": dashboard.description,
                "dashboard_type": dashboard.dashboard_type.value,
                "widgets": dashboard.widgets,
                "layout": dashboard.layout,
                "time_range": dashboard.time_range,
                "refresh_interval_seconds": dashboard.refresh_interval_seconds,
                "auto_refresh": dashboard.auto_refresh,
                "tags": dashboard.tags
            }
        }
        
        return export_data

    def import_dashboard(self, import_data: Dict[str, Any], imported_by: str) -> Dashboard:
        """Import dashboard from export data."""
        if "dashboard" not in import_data:
            raise ValueError("Invalid import data")
        
        dashboard_data = import_data["dashboard"]
        
        return self.create_dashboard(dashboard_data, imported_by)

    def get_service_statistics(self) -> Dict[str, Any]:
        """Get dashboard service statistics."""
        active_dashboards = len([d for d in self.dashboards.values() 
                               if d.last_viewed_at and 
                               (datetime.now(timezone.utc) - d.last_viewed_at).days < 7])
        
        self.service_stats["active_dashboards"] = active_dashboards
        
        return {
            **self.service_stats,
            "cache_hit_rate": (self.service_stats["cache_hits"] / 
                             max(self.service_stats["cache_hits"] + self.service_stats["cache_misses"], 1)) * 100,
            "cache_entries": len(self.data_cache),
            "template_count": len(self.dashboard_templates)
        }